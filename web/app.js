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

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Failed to start resolution process.');
        }

        const data = await response.json();
        const taskId = data.task_id;
        if (!taskId) {
            throw new Error(`The server did not return a task ID: ${JSON.stringify(data)}`);
        }
        logOutput.innerText += `[Pipeline] Task queued (ID: ${taskId.slice(0, 8)}...). Polling status...\n`;

        // Poll task status endpoint until done
        let completed = false;
        while (!completed) {
            await new Promise(r => setTimeout(r, 1500));
            const statusRes = await fetch(`/api/status/${taskId}`);
            if (!statusRes.ok) continue;

            const taskInfo = await statusRes.json();
            const status = taskInfo.status;

            // Update Issue Display Box if available
            if (taskInfo.issue_title) {
                document.getElementById('display-issue-title').innerText = taskInfo.issue_title;
                document.getElementById('display-issue-body').innerText = taskInfo.issue_body || '(No description provided)';
                document.getElementById('issue-display-card').classList.remove('hidden');
            }

            // Update Target Code Box if available
            if (taskInfo.target_file && taskInfo.target_content) {
                document.getElementById('display-target-file').innerText = taskInfo.target_file;
                document.getElementById('display-code-content').innerText = taskInfo.target_content;
                document.getElementById('code-display-card').classList.remove('hidden');
            }

            if (status === 'in_progress' || status === 'investigating') {
                setStepActive('step-investigate');
                logOutput.innerText = `[Pipeline] Task state: Investigating & scanning repo...`;
            } else if (status === 'executing') {
                setStepCompleted('step-investigate');
                setStepActive('step-execute');
                logOutput.innerText = `[Pipeline] Task state: Executing LLM patch...`;
            } else if (status === 'verifying') {
                setStepCompleted('step-investigate');
                setStepCompleted('step-execute');
                setStepActive('step-verify');
                logOutput.innerText = `[Pipeline] Task state: Running verification sandbox tests...`;
            } else if (status === 'resolved') {
                completed = true;
                setStepCompleted('step-investigate');
                setStepCompleted('step-execute');
                setStepCompleted('step-verify');
                setStepCompleted('step-resolve');

                logOutput.innerText = `[Success] Resolution complete!\n[Patch] ${taskInfo.patch || 'Fix applied successfully'}\n[PR] ${taskInfo.pr_url || 'PR created'}`;
                document.getElementById('result-desc').innerText = taskInfo.patch || 'Issue resolved automatically!';
                if (taskInfo.pr_url) {
                    document.getElementById('pr-link').href = taskInfo.pr_url;
                    document.getElementById('pr-link').classList.remove('hidden');
                } else {
                    document.getElementById('pr-link').classList.add('hidden');
                }
                resultBox.classList.remove('hidden');
            } else if (status === 'failed') {
                completed = true;
                logOutput.innerText = `[Error] Resolution failed!\nDetails: ${taskInfo.error_message || 'Tests failed or max retries reached.'}`;
            }
        }
    } catch (err) {
        logOutput.innerText += `\n[Error] Connection error: ${err.message}`;
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
