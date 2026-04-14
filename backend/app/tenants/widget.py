from flask import Blueprint, Response, jsonify
from app.logging_config import error_logger
import os

widget_bp = Blueprint('widget', __name__)

@widget_bp.route('/widget.js', methods=['GET'])
def get_widget_script():
    try:
        api_base_url = os.environ.get('API_BASE_URL', 'http://localhost:5000')
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

        js_content = f"""
(function() {{
    const scriptTag = document.currentScript;
    const tenantId = scriptTag.getAttribute('data-tenant-id');
    const apiBaseUrl = "{api_base_url}".replace(/\\/$/, "");
    const frontendUrl = "{frontend_url}".replace(/\\/$/, "");

    if (!tenantId) {{
        console.error('Burncodes AI Widget: data-tenant-id attribute is missing.');
        return;
    }}

    // Create container for the widget
    const container = document.createElement('div');
    container.id = 'burncodes-ai-widget-container';
    container.style.position = 'fixed';
    container.style.bottom = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'flex-end';
    document.body.appendChild(container);

    // Create Iframe
    const iframe = document.createElement('iframe');
    iframe.src = `${{frontendUrl}}/chat/${{tenantId}}?widget`;
    iframe.style.width = '400px';
    iframe.style.height = '600px';
    iframe.style.border = 'none';
    iframe.style.borderRadius = '10px';
    iframe.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    iframe.style.marginBottom = '10px';
    iframe.style.display = 'none'; // Hidden by default
    iframe.style.backgroundColor = 'white';
    container.appendChild(iframe);

    // Fetch Tenant Config for Launcher Appearance
    fetch(`${{apiBaseUrl}}/api/tenants/${{tenantId}}/public`)
        .then(response => response.json())
        .then(data => {{
            if (data.error) {{
                console.error('Burncodes AI Widget: Failed to load tenant config.', data.error);
                return;
            }}

            const config = data.widget_config || {{}};
            const styles = config.component_styles || {{}};
            const palette = config.color_palette || [];

            const getPaletteColor = (colorId) => {{
                const color = palette.find(c => c.id === colorId);
                return color ? color.value : colorId;
            }};

            const launcherBgColor = getPaletteColor(styles.launcher_background_color || 'c_primary') || '#A855F7';
            const launcherIcon = config.launcher_icon;

            // Create Launcher Button
            const launcher = document.createElement('div');
            launcher.style.width = '60px';
            launcher.style.height = '60px';
            launcher.style.borderRadius = '50%';
            launcher.style.backgroundColor = launcherBgColor;
            launcher.style.cursor = 'pointer';
            launcher.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
            launcher.style.display = 'flex';
            launcher.style.justifyContent = 'center';
            launcher.style.alignItems = 'center';
            launcher.style.transition = 'transform 0.2s';

            // Add Icon or Default
            if (launcherIcon) {{
                const img = document.createElement('img');
                img.src = launcherIcon;
                img.style.width = '30px';
                img.style.height = '30px';
                img.style.objectFit = 'contain';
                launcher.appendChild(img);
            }} else {{
                // Default Icon (Chat Bubble)
                launcher.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                `;
            }}

            launcher.addEventListener('mouseenter', () => {{
                launcher.style.transform = 'scale(1.1)';
            }});
            launcher.addEventListener('mouseleave', () => {{
                launcher.style.transform = 'scale(1.0)';
            }});

            launcher.addEventListener('click', () => {{
                if (iframe.style.display === 'none') {{
                    iframe.style.display = 'block';
                }} else {{
                    iframe.style.display = 'none';
                }}
            }});

            container.appendChild(launcher);
        }})
        .catch(err => {{
            console.error('Burncodes AI Widget: Error fetching config.', err);
        }});

}})();
"""
        return Response(js_content, mimetype='application/javascript')
    except Exception as e:
        error_logger.error(f"Error serving widget script: {e}", exc_info=True)
        return jsonify({"error": "Failed to serve widget script"}), 500
