targetScope = 'resourceGroup'

@minLength(3)
@maxLength(12)
param prefix string

param location string = resourceGroup().location
param imageTag string = 'latest'
param deployJob bool = false
param emailRecipient string = 'junghunlee@microsoft.com'

var suffix = uniqueString(subscription().subscriptionId, resourceGroup().id, prefix)
var registryName = take(toLower('${prefix}${suffix}'), 50)
var identityName = '${prefix}-job-identity'
var image = '${registryName}.azurecr.io/geo-monitor:${imageTag}'
var acrPullRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)
var communicationOwnerRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '09976791-48a7-449e-bb21-39d1a415f350'
)

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

resource registryPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, acrPullRoleId)
  scope: registry
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleId
  }
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-environment'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

resource emailService 'Microsoft.Communication/emailServices@2023-03-31' = {
  name: '${prefix}-email'
  location: 'global'
  properties: {
    dataLocation: 'United States'
  }
}

resource emailDomain 'Microsoft.Communication/emailServices/domains@2023-03-31' = {
  parent: emailService
  name: 'AzureManagedDomain'
  location: 'global'
  properties: {
    domainManagement: 'AzureManaged'
    userEngagementTracking: 'Disabled'
  }
}

resource communicationService 'Microsoft.Communication/communicationServices@2023-03-31' = {
  name: '${prefix}-communication'
  location: 'global'
  properties: {
    dataLocation: 'United States'
    linkedDomains: [
      emailDomain.id
    ]
  }
}

resource communicationRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(communicationService.id, identity.id, communicationOwnerRoleId)
  scope: communicationService
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: communicationOwnerRoleId
  }
}

resource job 'Microsoft.App/jobs@2024-03-01' = if (deployJob) {
  name: '${prefix}-hourly-job'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    environmentId: environment.id
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: 900
      replicaRetryLimit: 1
      scheduleTriggerConfig: {
        cronExpression: '0 * * * *'
        parallelism: 1
        replicaCompletionCount: 1
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'geo-monitor'
          image: image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'ACS_EMAIL_ENDPOINT'
              value: 'https://${communicationService.name}.communication.azure.com'
            }
            {
              name: 'EMAIL_SENDER'
              value: 'DoNotReply@${emailDomain.properties.mailFromSenderDomain}'
            }
            {
              name: 'EMAIL_RECIPIENT'
              value: emailRecipient
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: identity.properties.clientId
            }
          ]
        }
      ]
    }
  }
  dependsOn: [
    registryPull
    communicationRole
  ]
}

output registryName string = registry.name
output imageName string = image
output jobName string = deployJob ? job.name : ''
output emailSender string = 'DoNotReply@${emailDomain.properties.mailFromSenderDomain}'
