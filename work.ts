import { DataQuery } from '@grafana/schema';

export interface MyQuery extends DataQuery {
  queryType: string; // 'panel' or 'variable'
  ticketId: string;
  telemetryId: string;
}

export const defaultQuery: Partial<MyQuery> = {
  queryType: 'panel',
  ticketId: '',
  telemetryId: '',
};

export interface MyVariableQuery {
  ticketId: string;
}

export interface MyDataSourceOptions {}









import { DataSourcePlugin } from '@grafana/data';
import { DataSource } from './datasource';
import { ConfigEditor } from './components/ConfigEditor';
import { QueryEditor } from './components/QueryEditor';
import { VariableQueryEditor } from './components/VariableQueryEditor';
import { MyQuery, MyDataSourceOptions } from './types';

export const plugin = new DataSourcePlugin<DataSource, MyQuery, MyDataSourceOptions>(DataSource)
  .setConfigEditor(ConfigEditor)
  .setQueryEditor(QueryEditor)
  .setVariableQueryEditor(VariableQueryEditor);



document.addEventListener("DOMContentLoaded", function() {
    var btn = document.createElement('a');
    
    // Check if the current browser path contains the Japanese subfolder
    var currentPath = window.location.pathname;
    
    if (currentPath.includes('/ja/')) {
        // If viewing Japanese HTML, point to the Japanese PDF folder path
        btn.href = "../../current/pdf/pdf.pdf"; 
    } else {
        // If viewing English HTML, use the default path
        btn.href = "../pdf/pdf.pdf";
    }
    
    btn.target = "_blank";
    btn.innerHTML = "📥 Download PDF";

    // Matching your modern CSS styling
    btn.style.cssText = `
        position: fixed;
        bottom: 125px;
        left: 20px;
        background: #ffffff;
        padding: 8px 14px;
        border: 1px solid #e1e4e8;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(27,31,35,0.15);
        color: #24292e;
        text-decoration: none;
        cursor: pointer;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 13px;
        font-weight: 600;
        z-index: 9999;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 6px;
    `;

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


