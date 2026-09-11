document.getElementById('resolver-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const issueUrl = document.getElementById('issue-url').value;
    const repoPath = document.getElementById('repo-path').value;
    const githubToken = document.getElementById('github-token').value;

    const statusSection = document.getElementById('status-section');
    const submitBtn = document.getElementById('submit-btn');
    const logOutput = document.getElementById('log-output');
    const resultBox = document.getElementById('result-box');

    statusSection.classList.remove('hidden');
    resultBox.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.innerText = "⏳ Running Resolution Pipeline...";

    logOutput.innerText = "[Pipeline] Initializing agent state machine...\n";

    setStepActive('step-investigate');

    try {
        const response = await fetch('/api/resolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                issue_url: issueUrl,
                repo_path: repoPath,
                github_token: githubToken
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'resolved') {
            setStepCompleted('step-investigate');
            setStepCompleted('step-execute');
            setStepCompleted('step-verify');
            setStepCompleted('step-resolve');

            logOutput.innerText += `\n[Success] Resolution complete!\n[Patch] ${data.patch || 'Fix applied'}\n[PR] ${data.pr_url}`;
            
            document.getElementById('result-desc').innerText = `Issue resolved automatically! ${data.patch || ''}`;
            document.getElementById('pr-link').href = data.pr_url;
            resultBox.classList.remove('hidden');
        } else {
            logOutput.innerText += `\n[Error] Pipeline status: ${data.status.toUpperCase()}\nDetails: ${data.error_message || 'Tests failed or max retries reached.'}`;
        }
    } catch (err) {
        logOutput.innerText += `\n[Error] Failed to connect to server: ${err.message}`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "🚀 Launch AI Resolver";
    }
});

function setStepActive(stepId) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(stepId).classList.add('active');
}

function setStepCompleted(stepId) {
    document.getElementById(stepId).classList.add('completed');
}
