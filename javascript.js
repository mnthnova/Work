// Add these variables right above injectDiffControls
    let currentBranch = window.location.pathname.match(/\/([^\/]+)\/current\//) ? window.location.pathname.match(/\/([^\/]+)\/current\//)[1] : "";
    let targetBranch = currentBranch;
    let targetDeffPath = "previous"; // Keeping your exact variable name

    async function injectDiffControls() {
        if (document.getElementById('diff-settings-panel')) return;

        let panel = document.createElement('div');
        panel.id = 'diff-settings-panel';
        panel.style.cssText = 'position: fixed; bottom: 20px; left: 20px; background: white; padding: 10px; border: 2px solid #007bff; z-index: 999999; display: flex; gap: 10px; font-family: sans-serif; border-radius: 6px;';

        // 1. BRANCH DROPDOWN (Dynamically pulls from versions.json)
        let branchSelect = document.createElement('select');
        branchSelect.style.padding = "4px";
        try {
            let basePath = window.location.pathname.split(`/${currentBranch}/current/`)[0];
            let response = await fetch(`${basePath}/versions.json`);
            if (response.ok) {
                let versions = await response.json();
                versions.forEach(v => {
                    let opt = document.createElement('option');
                    opt.value = v.name;
                    opt.textContent = "Branch: " + v.name;
                    if (v.name === currentBranch) opt.selected = true;
                    branchSelect.appendChild(opt);
                });
            }
        } catch (e) {
            // Fallback if versions.json fails
            branchSelect.innerHTML = `<option value="${currentBranch}">Branch: ${currentBranch}</option>`;
        }

        // 2. COMMIT DROPDOWN
        let commitSelect = document.createElement('select');
        commitSelect.style.padding = "4px";
        commitSelect.innerHTML = `
            <option value="current">Current Version</option>
            <option value="previous" selected>Previous Commit (-1)</option>
            <option value="prev-2">Older Commit (-2)</option>
        `;

        // --- THE CACHE FIX IS HERE ---
        // When you change a dropdown, we set previousHTML to null so it forgets the old data!
        branchSelect.addEventListener('change', function(e) {
            targetBranch = e.target.value;
            previousHTML = null; 
            if (diffActive) toggleDiff(); // Auto-turn off diff to reset screen
        });

        commitSelect.addEventListener('change', function(e) {
            targetDeffPath = e.target.value;
            previousHTML = null; 
            if (diffActive) toggleDiff(); // Auto-turn off diff to reset screen
        });

        panel.appendChild(branchSelect);
        panel.appendChild(commitSelect);
        document.body.appendChild(panel);
    }

    // Call it safely
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        injectDiffControls();
    } else {
        document.addEventListener('DOMContentLoaded', injectDiffControls);
    }

    // 3. CROSS-BRANCH URL ROUTER
    function getPreviousURL() {
        let path = window.location.pathname;
        
        // Plucks out "/main/current/" and replaces it with whatever branch/commit you selected
        let searchString = `/${currentBranch}/current/`;
        let replaceString = `/${targetBranch}/${targetDeffPath}/`;
        
        return path.replace(searchString, replaceString);
    }
