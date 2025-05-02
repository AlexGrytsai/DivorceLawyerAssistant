divorce_profiler@vm-free:~/n8n$ docker-compose logs
n8n_local  | User settings loaded from: /home/node/.n8n/config
n8n_local  | Initializing n8n process
n8n_local  | n8n ready on 0.0.0.0, port 5678
n8n_local  | n8n Task Broker ready on 127.0.0.1, port 5679
n8n_local  | Version: 1.89.2
n8n_local  |  ================================
n8n_local  |    Start Active Workflows:
n8n_local  |  ================================
n8n_local  | Task runner connection attempt failed with status code 403
n8n_local  | Task runner connection attempt failed with status code 403
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at ActiveWorkflowManager.activateWorkflow (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:300:34)
n8n_local  |     at /usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:289:17
n8n_local  |     at async Promise.all (index 0)
n8n_local  |     at ActiveWorkflowManager.addActiveWorkflows (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:291:13)
n8n_local  |     at ActiveWorkflowManager.init (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:92:9)
n8n_local  |     at Start.run (/usr/local/lib/node_modules/n8n/dist/commands/start.js:258:9)
n8n_local  |     at Start._run (/usr/local/lib/node_modules/n8n/node_modules/@oclif/core/lib/command.js:302:22)
n8n_local  |     at Config.runCommand (/usr/local/lib/node_modules/n8n/node_modules/@oclif/core/lib/config/config.js:424:25)
n8n_local  |     at run (/usr/local/lib/node_modules/n8n/node_modules/@oclif/core/lib/main.js:94:16)
n8n_local  |     at /usr/local/lib/node_modules/n8n/bin/n8n:70:2
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |      => ERROR: Workflow "Assistant" (ID: 5mO1xXAeOfc6BmGv) could not be activated on first try, keep on trying if not an auth issue
n8n_local  |                There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | Issue on initial workflow activation try of "Assistant" (ID: 5mO1xXAeOfc6BmGv) (startup)
n8n_local  | 
n8n_local  | Editor is now accessible via:
n8n_local  | https://lamb-fit-rationally.ngrok-free.app
n8n_local  | Calling Error Workflow for "5mO1xXAeOfc6BmGv". Could not find "n8n-nodes-base.errorTrigger" in workflow "5mO1xXAeOfc6BmGv"
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 2 seconds
n8n_local  | Registered runner "JS Task Runner" (aiFmR5OzNjEl0W4Dc8t-T) 
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 4 seconds
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 8 seconds
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 16 seconds
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 32 seconds
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 64 seconds
n8n_local  | Try to activate workflow "Assistant" (5mO1xXAeOfc6BmGv)
n8n_local  | There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  | WorkflowActivationError: There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."
n8n_local  |     at ActiveWorkflows.add (/usr/local/lib/node_modules/n8n/node_modules/n8n-core/dist/execution-engine/active-workflows.js:64:23)
n8n_local  |     at processTicksAndRejections (node:internal/process/task_queues:95:5)
n8n_local  |     at ActiveWorkflowManager.addTriggersAndPollers (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:534:13)
n8n_local  |     at ActiveWorkflowManager.add (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:389:17)
n8n_local  |     at Timeout.retryFunction [as _onTimeout] (/usr/local/lib/node_modules/n8n/dist/active-workflow-manager.js:451:17)
n8n_local  | 
n8n_local  | The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
n8n_local  |  -> Activation of workflow "Assistant" (5mO1xXAeOfc6BmGv) did fail with error: "There was a problem activating the workflow: "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client."" | retry in 128 seconds