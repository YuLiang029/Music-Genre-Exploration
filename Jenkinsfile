properties([pipelineTriggers([githubPush()])])
void setBuildStatus(String message, String state) {
  step([
      $class: "GitHubCommitStatusSetter",
      reposSource: [$class: "ManuallyEnteredRepositorySource", url: "https://github.com/YuLiang029/spotify-experiment-framework"],
      contextSource: [$class: "ManuallyEnteredCommitContextSource", context: "ci/jenkins/build-status"],
      errorHandlers: [[$class: "ChangingBuildStatusErrorHandler", result: "UNSTABLE"]],
      statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}
def buildBadge = addEmbeddableBadgeConfiguration(id: "build", subject: "spotify-experiment-framework Build");

pipeline {
  agent {
    docker {
      image 'shadash/tuneblendr-context'
    }
  }
  options {
	skipStagesAfterUnstable()
  }
  stages {
    stage('test build context') {
      steps {
		sh 'docker --version && docker-compose --version'
      }
    }
    stage('prepare') {
      steps {
        setBuildStatus("Building...", "PENDING");
        script{ buildBadge.setStatus('running'); }
      }
    }

    stage('build') {
        steps {
          sh 'docker build -t yliang/spotify-experiment-framework:latest .'
        }
    }

	stage('deploy') {
	  when {
	    branch 'master'
	  }
	  steps {
		sh 'docker stack deploy -c docker-compose.yml spotify-experiment-framework'
	  }
	}

  }
  post {
    always {
      echo 'build finished'
    }
    success {
	  setBuildStatus("Build succeeded", "SUCCESS");
	  script{ buildBadge.setStatus('passing'); }
    }
    failure {
      setBuildStatus("Build failed", "FAILURE");
  	  script{ buildBadge.setStatus('failing'); }
    }
  }
}
