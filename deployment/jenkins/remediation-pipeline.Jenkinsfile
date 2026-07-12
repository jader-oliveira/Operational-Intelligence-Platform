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
// AWX_JOB_TEMPLATE below is a placeholder: the three remediation-type job
// templates (storage vMotion, k8s workload resize/restart, config revert)
// from the MVP plan's weeks 6-7 have not been written yet. Wire the real
// template name in once it exists — do not point this at a template you
// haven't reviewed.

pipeline {
    agent any

    parameters {
        string(name: 'recommendation_id', defaultValue: '', description: 'boip recommendation.id')
        string(name: 'incident_id', defaultValue: '', description: 'boip incident.id')
        string(name: 'risk', defaultValue: 'medium', description: 'low | medium | high | critical')
    }

    environment {
        BOIP_CORE_URL = credentials('boip-core-url')
        AWX_JOB_TEMPLATE = 'CHANGE-ME-not-yet-built'
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
                echo "Would launch AWX job template ${AWX_JOB_TEMPLATE} for recommendation ${params.recommendation_id}."
                echo 'Not wired yet — see comment at top of this file. Fails closed until it is.'
                error('AWX_JOB_TEMPLATE is a placeholder — wire the real template before enabling execution.')
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
