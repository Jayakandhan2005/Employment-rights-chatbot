# File: /social-media-analyzer/social-media-analyzer/src/views/components.py
import streamlit as st
from constants.icons import SOCIAL_ICONS
def display_issue_detection(issues, keyword):
    """Display detected issues with recommendations"""
    if not issues:
        st.warning("No issues detected.")
        return
        
    st.markdown('<div class="issue-detection">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="issue-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4b6cb7">
                <path d="M12 2L1 21h22L12 2zm0 3.5L18.5 19h-13L12 5.5z"/>
                <path d="M12 16c.8 0 1.5-.7 1.5-1.5S12.8 13 12 13s-1.5.7-1.5 1.5.7 1.5 1.5 1.5zm-1-5h2v-4h-2v4z"/>
            </svg>
            Detected Issues for {keyword}
        </div>
    """, unsafe_allow_html=True)

    for issue in issues:
        st.markdown('<div class="issue-card">', unsafe_allow_html=True)
        
        # Issue title and stats
        st.markdown(f"""
        <div class="issue-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#e74c3c">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            {issue['name']} Issues
        </div>
        <div class="issue-stats">
            <div class="issue-stat">
                <span class="issue-stat-value">{len(issue.get('posts', []))}</span> reports
            </div>
            <div class="issue-stat">
                <span class="issue-stat-value">{issue['engagement']:,}</span> engagement
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Example posts (collapsible)
        actual_post_count = len(issue.get('posts', []))
        with st.expander(f"See {actual_post_count} example posts"):
            if actual_post_count > 0:
                for post in issue.get('posts', []):
                    platform = post.get('platform', 'Unknown')
                    platform_icon = SOCIAL_ICONS.get(platform, "")
                    url = post.get('url', '#')
                    
                    st.markdown(f'''
                    <div class="post-card {platform.lower()}">
                        <div class="platform-tag {platform.lower()}">
                            <span class="icon-container">{platform_icon}</span>{platform}
                        </div>
                        <div style="display:flex;align-items:center;gap:10px;">
                            <p class="post-content">{post['content']}</p>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="sentiment-badge negative">Negative</div>
                            <a href="{url}" target="_blank" class="view-source-btn">
                                <button style="background-color: #4b6cb7; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">
                                    View Source
                                </button>
                            </a>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.info("No example posts available for this issue.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
        st.markdown('</div>', unsafe_allow_html=True)
def display_recommendations(recommendations):
    """Display generated recommendations with enhanced UI"""
    if not recommendations:
        return
    
    st.markdown('<div class="response-templates">', unsafe_allow_html=True)
    st.markdown("""
        <div class="template-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4b6cb7">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
            </svg>
            Recommended Actions
        </div>
    """, unsafe_allow_html=True)
    
    for i, rec in enumerate(recommendations):
        rec_key = f"rec_{i}"
        
        if rec_key not in st.session_state:
            st.session_state[rec_key] = {
                "editing": False,
                "content": rec.get("content", ""),
                "type": rec.get("type", "General Recommendation")
            }
        
        st.markdown(f'''
        <div class="template-card">
            <div class="template-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4b6cb7">
                    <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                </svg>
                {rec.get("type", "Recommendation")}
            </div>
            <div class="template-content">
                {st.session_state[rec_key]["content"]}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
def display_response_templates(templates):
    """Display generated response templates with enhanced UI and brand specificity"""
    if not templates:
        return
    
    st.markdown('<div class="response-templates">', unsafe_allow_html=True)
    st.markdown("""
    <div class="template-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4b6cb7">
            <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
        </svg>
        Brand-Specific Response Templates
    </div>
    """, unsafe_allow_html=True)
    
    for i, template in enumerate(templates):
        template_key = f"template_{template['template_id']}"
        
        if template_key not in st.session_state:
            st.session_state[template_key] = {
                "editing": False,
                "template": template["template"],
                "brand": template["brand"],
                "generated_at": template["generated_at"]
            }
        
        st.markdown(f'''
        <div class="template-card">
            <div class="template-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4b6cb7">
                    <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                </svg>
                {template["issue"]} Response for {template["brand"]}
                <span style="font-size: 0.8em; color: #666; margin-left: 10px;">ID: {template["template_id"]}</span>
            </div>
        ''', unsafe_allow_html=True)
        
        if st.session_state[template_key]["editing"]:
            edited_template = st.text_area(
                "Edit the template:", 
                value=st.session_state[template_key]["template"],
                key=f"editor_{template_key}",
                height=200
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", key=f"save_{template_key}"):
                    st.session_state[template_key]["template"] = edited_template
                    st.session_state[template_key]["editing"] = False
                    st.success("Template updated successfully!")
            with col2:
                if st.button("❌ Cancel", key=f"cancel_{template_key}"):
                    st.session_state[template_key]["editing"] = False
                    st.rerun()
        else:
            st.markdown(f'''
            <div class="template-content">
                <div style="margin-bottom: 10px; color: #666;">
                    Generated: {template["generated_at"]}
                </div>
                {st.session_state[template_key]["template"]}
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('<div class="template-actions">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✏ Edit Template", key=f"edit_{template_key}"):
                    st.session_state[template_key]["editing"] = True
                    st.rerun()
            
            with col2:
                if st.button("📋 Use Template", key=f"use_{template_key}"):
                    st.code(st.session_state[template_key]["template"], language="markdown")
                    st.success("Template ready to use! Copy the content above.")
            
            with col3:
                if st.button("📝 Copy to Clipboard", key=f"copy_{template_key}"):
                    st.session_state.copied_template = st.session_state[template_key]["template"]
                    st.success("Template copied to clipboard!")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    

def display_crisis_alert(crisis_data):
    st.markdown(f'''
    <div class="crisis-alert">
        <div class="crisis-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="white">
                <path d="M12 2L1 21h22L12 2zm0 3.5L18.5 19h-13L12 5.5z"/>
                <path d="M12 16c.8 0 1.5-.7 1.5-1.5S12.8 13 12 13s-1.5.7-1.5 1.5.7 1.5 1.5 1.5zm-1-5h2v-4h-2v4z"/>
            </svg>
            Potential PR Crisis Detected
        </div>
        <p>{crisis_data["description"]}</p>
        <div class="crisis-metrics">
            <div class="crisis-metric">
                <div class="crisis-metric-value">{crisis_data["posts"]}</div>
                <div class="crisis-metric-label">Mentions</div>
            </div>
            <div class="crisis-metric">
                <div class="crisis-metric-value">{crisis_data["percentage"]}%</div>
                <div class="crisis-metric-label">Negative Sentiment</div>
            </div>
            <div class="crisis-metric">
                <div class="crisis-metric-value">{crisis_data["engagement"]}</div>
                <div class="crisis-metric-label">Engagement</div>
            </div>
        </div>
        <a href="#crisis-posts-section" class="view-crisis-btn">View Crisis Details</a>
    </div>
    ''', unsafe_allow_html=True)
