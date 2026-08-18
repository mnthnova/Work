// Ensure these variables are at the top
    let currentBranch = window.location.pathname.match(/\/([^\/]+)\/current\//) ? window.location.pathname.match(/\/([^\/]+)\/current\//)[1] : "";
    let targetBranch = ""; // Will be dynamically set

    async function injectDiffControls() {
        if (document.getElementById('diff-settings-panel')) return;

        let panel = document.createElement('div');
        panel.id = 'diff-settings-panel';
        panel.style.cssText = `
            position: fixed; 
            bottom: 20px; 
            left: 20px; 
            background: #ffffff; 
            padding: 10px 12px; 
            border: 1px solid #e1e4e8; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(27,31,35,0.15); 
            z-index: 999999; 
            display: flex; 
            flex-direction: column; 
            gap: 6px; 
            width: 180px; 
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        `;

        // A sleek label to explain what the dropdown does
        let label = document.createElement('div');
        label.textContent = "Compare against:";
        label.style.cssText = "font-size: 11px; font-weight: 600; color: #586069; margin-left: 2px;";
        panel.appendChild(label);

        const selectStyle = `
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 6px 8px; 
            font-size: 13px;
            font-weight: 500;
            color: #24292e;
            cursor: pointer;
            outline: none;
            width: 100%; 
            box-sizing: border-box;
            transition: all 0.2s ease;
        `;

        // 1. THE SINGLE TARGET DROPDOWN
        let branchSelect = document.createElement('select');
        branchSelect.style.cssText = selectStyle;

        // Fetch and Sort the JSON
        try {
            let basePath = window.location.pathname.split(`/${currentBranch}/current/`)[0];
            let response = await fetch(`${basePath}/versions.json`);
            if (response.ok) {
                let versions = await response.json();
                
                let branchGroup = document.createElement('optgroup');
                branchGroup.label = "── Branches ──";
                
                let tagGroup = document.createElement('optgroup');
                tagGroup.label = "── Tags (Releases) ──";

                versions.forEach(v => {
                    let opt = document.createElement('option');
                    opt.value = v.name;
                    opt.textContent = v.name;
                    opt.setAttribute('data-type', v.type);

                    if (v.type === 'tag') {
                        tagGroup.appendChild(opt);
                    } else {
                        branchGroup.appendChild(opt);
                    }
                });

                branchSelect.appendChild(branchGroup);
                branchSelect.appendChild(tagGroup);

                // SMART DEFAULT SELECTION:
                // Try to default the compare target to 'main' (if we aren't already on main)
                // Otherwise, pick the first available option that isn't the current branch.
                let selectedIndex = 0;
                for (let i = 0; i < branchSelect.options.length; i++) {
                    if (branchSelect.options[i].value === 'main' && currentBranch !== 'main') {
                        selectedIndex = i;
                        break;
                    } else if (branchSelect.options[i].value !== currentBranch && selectedIndex === 0) {
                        selectedIndex = i;
                    }
                }
                branchSelect.selectedIndex = selectedIndex;
                targetBranch = branchSelect.value;
            }
        } catch (e) {
            branchSelect.innerHTML = `<option value="main">main</option>`;
            targetBranch = "main";
        }

        // --- THE EVENT LISTENER ---
        branchSelect.addEventListener('change', function(e) {
            targetBranch = e.target.value;
            previousHTML = null; // Instantly clear cache so it fetches the newly selected branch
            if (diffActive) toggleDiff(); 
        });

        panel.appendChild(branchSelect);
        document.body.appendChild(panel);
    }

    // Call it safely
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        injectDiffControls();
    } else {
        document.addEventListener('DOMContentLoaded', injectDiffControls);
    }

    // 2. THE SIMPLIFIED URL ROUTER
    function getPreviousURL() {
        let path = window.location.pathname;
        
        // All we do now is swap the currently viewed branch with the target branch!
        // Both always look inside their respective /current/ folders.
        let searchString = `/${currentBranch}/current/`;
        let replaceString = `/${targetBranch}/current/`;
        
        return path.replace(searchString, replaceString);
    }
