// The approval gate from ADR 0015 (amended: Jenkins/CloudBees, not GitLab —
// this cluster runs neither GitLab nor a GitLab-equivalent, and Jenkins/
// CloudBees is already deployed and trusted here).
//
// boip-core's propose_recommendation() triggers this job. Triggering it is
// NOT the approval — the pipeline itself blocks on the `input` step below
// until a human clicks approve. Nothing in boip-core or this pipeline calls
// AWX before that happens. This is ADR 0001 (human approval before
// production change) enforced as infrastructure, not a comment.
//
// Status as of ADR 0018: one real remediation type exists —
// boip-revert-config (AWX job template id 9, playbook
// deployment/ansible/remediations/revert-config.yml, synced from this repo).
// It has NO credential attached in AWX, so it cannot execute against
// vCenter yet — attach a real vCenter machine credential there first.
// The 'awx-api-token' Jenkins credential exists and is read-only-safe to
// use for the status check below; the actual launch call is still
// commented out because its shell script has not been exercised against
// a real Jenkins agent in this environment — do not enable it without
// testing on a non-production job first.

pipeline {
    agent any

    parameters {
        string(name: 'recommendation_id', defaultValue: '', description: 'boip recommendation.id')
        string(name: 'incident_id', defaultValue: '', description: 'boip incident.id')
        string(name: 'risk', defaultValue: 'medium', description: 'low | medium | high | critical')
    }

    environment {
        BOIP_CORE_URL = credentials('boip-core-url')
        AWX_URL = 'https://awx.breutech-solutions.be'
        AWX_JOB_TEMPLATE_ID = '9'
        AWX_JOB_TEMPLATE_NAME = 'boip-revert-config'
    }

    stages {
        stage('Fetch recommendation') {
            steps {
                sh '''
                    curl -sf "$BOIP_CORE_URL/incidents/$incident_id" \
                      | tee recommendation.json
                '''
            }
        }

        stage('Await approval') {
            steps {
                timeout(time: 24, unit: 'HOURS') {
                    input message: "Approve remediation for incident #${params.incident_id} (risk: ${params.risk})?",
                          submitter: (params.risk == 'high' || params.risk == 'critical') ? 'senior-engineers' : 'engineers'
                }
            }
        }

        stage('Execute via AWX') {
            steps {
                withCredentials([string(credentialsId: 'awx-api-token', variable: 'AWX_TOKEN')]) {
                    sh '''
                        echo "Checking AWX job template ${AWX_JOB_TEMPLATE_NAME} (id ${AWX_JOB_TEMPLATE_ID}) for an attached credential..."
                        curl -sf -H "Authorization: Bearer $AWX_TOKEN" \
                             "$AWX_URL/api/v2/job_templates/${AWX_JOB_TEMPLATE_ID}/" -o job_template.json
                        cat job_template.json
                    '''
                }
                // Deliberately not launching: (1) no vCenter credential is attached to
                // the job template yet, and (2) the launch call itself hasn't been
                // exercised against a real Jenkins agent in this environment. Both must
                // be resolved and verified — on a non-production job first — before
                // this stage should call POST /api/v2/job_templates/{id}/launch/.
                error("Execution intentionally disabled — see comment above stage('Execute via AWX').")
            }
        }

        stage('Verify') {
            steps {
                echo 'Runs the recommendation.verification checks from boip-core once execution is wired.'
            }
        }
    }

    post {
        always {
            echo "boip incident #${params.incident_id}, recommendation #${params.recommendation_id}: pipeline ${currentBuild.currentResult}"
        }
    }
}
