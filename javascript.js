async function injectDiffControls() {
        if (document.getElementById('diff-settings-panel')) return;

        let panel = document.createElement('div');
        panel.id = 'diff-settings-panel';
        
        // MODERN PANEL CSS
        panel.style.cssText = `
            position: fixed; 
            bottom: 20px; 
            left: 20px; 
            background: #ffffff; 
            padding: 12px 16px; 
            border: 1px solid #e1e4e8; 
            border-radius: 8px; 
            box-shadow: 0 4px 12px rgba(27,31,35,0.15); 
            z-index: 999999; 
            display: flex; 
            gap: 12px; 
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        `;

        // REUSABLE MODERN SELECT CSS
        const selectStyle = `
            appearance: none;
            -webkit-appearance: none;
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 6px 28px 6px 12px;
            font-size: 13px;
            font-weight: 500;
            color: #24292e;
            cursor: pointer;
            outline: none;
            transition: all 0.2s ease;
            background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%2324292e%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
            background-repeat: no-repeat;
            background-position: right 10px top 50%;
            background-size: 10px auto;
        `;

        // 1. BRANCH DROPDOWN
        let branchSelect = document.createElement('select');
        branchSelect.style.cssText = selectStyle;
        
        // Hover effect listener
        branchSelect.addEventListener('mouseenter', () => branchSelect.style.backgroundColor = '#e1e4e8');
        branchSelect.addEventListener('mouseleave', () => branchSelect.style.backgroundColor = '#f6f8fa');

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
            branchSelect.innerHTML = `<option value="${currentBranch}">Branch: ${currentBranch}</option>`;
        }

        // 2. COMMIT DROPDOWN
        let commitSelect = document.createElement('select');
        commitSelect.style.cssText = selectStyle;
        
        // Hover effect listener
        commitSelect.addEventListener('mouseenter', () => commitSelect.style.backgroundColor = '#e1e4e8');
        commitSelect.addEventListener('mouseleave', () => commitSelect.style.backgroundColor = '#f6f8fa');

        commitSelect.innerHTML = `
            <option value="current">Current Version</option>
            <option value="previous" selected>Previous Commit (-1)</option>
            <option value="prev-2">Older Commit (-2)</option>
        `;

        // LOGIC PRESERVED
        branchSelect.addEventListener('change', function(e) {
            targetBranch = e.target.value;
            previousHTML = null; 
            if (diffActive) toggleDiff(); 
        });

        commitSelect.addEventListener('change', function(e) {
            targetDeffPath = e.target.value;
            previousHTML = null; 
            if (diffActive) toggleDiff(); 
        });

        panel.appendChild(branchSelect);
        panel.appendChild(commitSelect);
        document.body.appendChild(panel);
    }




document.addEventListener("DOMContentLoaded", function() {
    var btn = document.createElement('div');
    
    // MODERN FLOATING BUTTON CSS
    btn.style.cssText = `
        position: fixed;
        bottom: 85px; /* Sits right above the diff panel */
        left: 20px;
        background: #ffffff;
        padding: 8px 14px;
        border: 1px solid #e1e4e8;
        border-radius: 20px; /* Pill shape */
        box-shadow: 0 4px 12px rgba(27,31,35,0.15);
        color: #24292e;
        cursor: pointer;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 13px;
        font-weight: 600;
        z-index: 9999;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    `;

    // Add sleek hover effect
    btn.addEventListener('mouseenter', () => {
        btn.style.borderColor = '#0366d6';
        btn.style.color = '#0366d6';
    });
    btn.addEventListener('mouseleave', () => {
        btn.style.borderColor = '#e1e4e8';
        btn.style.color = '#24292e';
    });

    var currentPath = window.location.pathname;

    if (currentPath.includes('/ja/')) {
        btn.innerHTML = "🌐 Switch To English";
        btn.onclick = function() {
            window.location.href = currentPath.replace('/ja/', '/');
        };
    } else {
        btn.innerHTML = "🌐 日本語 (Japanese)";
        btn.onclick = function() {
            var newPath = currentPath.replace(/(.*\/)(.*\.html)$/, '$1ja/$2');
            window.location.href = newPath;
        };
    }
    
    document.body.appendChild(btn);
});



















document.addEventListener("DOMContentLoaded", function() {
    var btn = document.createElement('a');
    btn.href = "../pdf/pdf.pdf";
    btn.target = "_blank";
    
    // MATCHING MODERN CSS
    btn.style.cssText = `
        position: fixed;
        bottom: 130px; /* Sits right above the Language button */
        left: 20px;
        background: #ffffff;
        padding: 8px 14px;
        border: 1px solid #e1e4e8;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(27,31,35,0.15);
        color: #24292e;
        text-decoration: none;
        cursor: pointer;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 13px;
        font-weight: 600;
        z-index: 9999;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 6px;
    `;

    btn.innerHTML = '<i class="fa fa-file-pdf-o" style="color: #d73a49;"></i> Download PDF';

    // Add sleek hover effect
    btn.addEventListener('mouseenter', () => {
        btn.style.borderColor = '#0366d6';
        btn.style.color = '#0366d6';
    });
    btn.addEventListener('mouseleave', () => {
        btn.style.borderColor = '#e1e4e8';
        btn.style.color = '#24292e';
    });

    document.body.appendChild(btn);
});
