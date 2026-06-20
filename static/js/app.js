// Skill Manager — frontend orchestration.
// Coordinates the three tabs (import / install / distribute) and the side panel.

(function () {
    'use strict';

    const state = {
        allSkills: [],          // for distribute view
        currentDetail: null,    // {source, name} for the open side panel
    };

    /* ---------- helpers ---------- */

    function $(sel, root = document) {
        return root.querySelector(sel);
    }

    function $$(sel, root = document) {
        return Array.from(root.querySelectorAll(sel));
    }

    function escapeHtml(text) {
        return String(text || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatBytes(n) {
        if (!n) return '0 B';
        const u = ['B', 'KB', 'MB', 'GB'];
        let i = 0;
        while (n >= 1024 && i < u.length - 1) {
            n /= 1024;
            i++;
        }
        return n.toFixed(n < 10 ? 1 : 0) + ' ' + u[i];
    }

    function formatTime(ts) {
        if (!ts) return '—';
        const d = new Date(ts * 1000);
        return d.toLocaleString();
    }

    function toast(msg, kind = 'success') {
        const el = document.createElement('div');
        el.className = 'toast ' + kind;
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2400);
    }

    async function api(path, options = {}) {
        const res = await fetch(path, {
            headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
            ...options,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok && !data.success) {
            throw new Error(data.error || data.message || `HTTP ${res.status}`);
        }
        return data;
    }

    function showMessage(el, text, kind) {
        el.textContent = text;
        el.className = 'message show ' + kind;
    }

    /* ---------- clock ---------- */

    function updateTime() {
        const el = $('#currentTime');
        if (el) el.textContent = new Date().toLocaleString();
    }

    /* ---------- tab switching ---------- */

    function setupTabs() {
        $$('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                $$('.tab').forEach(t => t.classList.remove('active'));
                $$('.panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                $('#' + tab.dataset.tab).classList.add('active');
            });
        });
    }

    /* ---------- import tab ---------- */

    function renderClaudeSkills(data) {
        const container = $('#claudeSkills');
        if (!data.skills.length) {
            container.innerHTML = '<div style="color: var(--text-muted)">暂无 skills</div>';
            return;
        }
        container.innerHTML = data.skills.map(skill => `
            <div class="skill-card" data-source="claude" data-name="${escapeHtml(skill.name)}">
                <div class="skill-name">
                    <input type="checkbox" class="skill-checkbox" onclick="event.stopPropagation()">
                    <span class="skill-name-text">${escapeHtml(skill.name)}</span>
                    <button class="btn-icon btn-open-folder" title="在文件管理器中打开"
                            data-source="claude" data-name="${escapeHtml(skill.name)}">📁</button>
                </div>
                <div class="skill-desc">${escapeHtml(skill.description || '无描述')}</div>
            </div>
        `).join('');

        $$('.skill-card[data-source="claude"]', container).forEach(card => {
            card.addEventListener('click', e => {
                if (e.target.closest('button, input')) return;
                openSkillDetail(card.dataset.source, card.dataset.name);
            });
        });
        bindOpenFolderButtons(container);
    }

    function renderOpenclawSkills(data) {
        const container = $('#openclawWorkspaces');
        if (!data.workspaces.length) {
            container.innerHTML = '<div style="color: var(--text-muted)">未找到 OpenCLAW workspaces</div>';
            $('#workspaceCheckboxes').innerHTML = '';
            return;
        }

        let wsCbs = '<div class="checkbox-group" style="margin-top: 12px;">';
        wsCbs += '<span style="color: var(--text-muted); font-size: 12px; width: 100%; margin-bottom: 6px;">同时安装到 OpenCLAW Workspace:</span>';

        container.innerHTML = data.workspaces.map(ws => {
            wsCbs += `
                <label class="checkbox-item">
                    <input type="checkbox" class="workspace-checkbox" value="${escapeHtml(ws.name)}">
                    ${escapeHtml(ws.name)}
                </label>
            `;
            return `
                <div class="workspace-section">
                    <div class="workspace-title">${escapeHtml(ws.name)}${ws.exists ? '' : ' <span style="color:var(--warning)">(skills 目录不存在)</span>'}</div>
                    <div class="skills-grid">
                        ${ws.skills.length === 0
                            ? '<span style="color: var(--text-muted); font-size: 12px;">暂无 skills</span>'
                            : ws.skills.map(skill => `
                                <div class="skill-card" data-source="${escapeHtml(ws.name)}" data-name="${escapeHtml(skill.name)}">
                                    <div class="skill-name">
                                        <input type="checkbox" class="skill-checkbox" onclick="event.stopPropagation()">
                                        <span class="skill-name-text">${escapeHtml(skill.name)}</span>
                                        <button class="btn-icon btn-open-folder" title="在文件管理器中打开"
                                                data-source="${escapeHtml(ws.name)}" data-name="${escapeHtml(skill.name)}">📁</button>
                                    </div>
                                    <div class="skill-desc">${escapeHtml(skill.description || '无描述')}</div>
                                </div>
                            `).join('')}
                    </div>
                </div>
            `;
        }).join('');

        wsCbs += '</div>';
        $('#workspaceCheckboxes').innerHTML = wsCbs;

        $$('.skill-card[data-source]', container).forEach(card => {
            card.addEventListener('click', e => {
                if (e.target.closest('button, input')) return;
                openSkillDetail(card.dataset.source, card.dataset.name);
            });
        });
        bindOpenFolderButtons(container);
    }

    async function openSkillFolder(source, name, btn) {
        if (btn) {
            btn.disabled = true;
            btn.classList.add('loading');
        }
        try {
            const data = await api(
                `/api/skills/${encodeURIComponent(source)}/${encodeURIComponent(name)}/open`,
                { method: 'POST' }
            );
            toast(data.message || '已请求打开', data.success ? 'success' : 'error');
        } catch (e) {
            toast('打开失败: ' + e.message, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('loading');
            }
        }
    }

    function bindOpenFolderButtons(root) {
        $$('.btn-open-folder', root).forEach(btn => {
            btn.addEventListener('click', e => {
                e.stopPropagation();
                openSkillFolder(btn.dataset.source, btn.dataset.name, btn);
            });
        });
    }

    function prepareDistributeSkills(data) {
        state.allSkills = [];
        data.claude.skills.forEach(s => state.allSkills.push({ ...s, source: 'Claude Code' }));
        data.openclaw.workspaces.forEach(ws => {
            ws.skills.forEach(s => state.allSkills.push({ ...s, source: `OpenCLAW ${ws.name}` }));
        });

        const container = $('#distributeSkills');
        if (!state.allSkills.length) {
            container.innerHTML = '<div style="color: var(--text-muted)">暂无 skills 可分发</div>';
            return;
        }

        container.innerHTML = state.allSkills.map((skill, idx) => `
            <div class="skill-card">
                <div class="skill-name">
                    <input type="checkbox" class="distribute-checkbox" data-idx="${idx}">
                    ${escapeHtml(skill.name)}
                </div>
                <div class="skill-desc">来源: ${escapeHtml(skill.source)}</div>
            </div>
        `).join('');
    }

    async function importSkills() {
        $('#claudeSkills').innerHTML = '<div class="loading">加载中</div>';
        $('#openclawWorkspaces').innerHTML = '<div class="loading">加载中</div>';
        try {
            const data = await api('/api/import-skills');
            renderClaudeSkills(data.claude);
            renderOpenclawSkills(data.openclaw);
            prepareDistributeSkills(data);
        } catch (e) {
            $('#claudeSkills').innerHTML =
                '<div class="message error show">加载失败: ' + escapeHtml(e.message) + '</div>';
        }
    }

    /* ---------- install tab ---------- */

    async function installSkillhub() {
        const msg = $('#installMsg');
        msg.style.display = 'block';
        msg.className = 'message show';
        msg.textContent = '正在安装 Skillhub CLI…';
        try {
            const data = await api('/api/install-skillhub', { method: 'POST' });
            showMessage(msg, data.message, data.success ? 'success' : 'error');
            if (data.success) importSkills();
        } catch (e) {
            showMessage(msg, '安装失败: ' + e.message, 'error');
        }
    }

    async function installSkill() {
        const skillName = $('#skillName').value.trim();
        const targets = [];
        if ($('#targetClaude').checked) targets.push('claude');
        $$('.workspace-checkbox:checked').forEach(cb => targets.push(cb.value));

        const msg = $('#installMsg');
        msg.style.display = 'block';
        msg.className = 'message show';
        msg.textContent = '正在安装…';

        if (!skillName) {
            showMessage(msg, '请输入技能名称', 'error');
            return;
        }
        if (!targets.length) {
            showMessage(msg, '请选择至少一个安装目标', 'error');
            return;
        }

        try {
            const data = await api('/api/install-skill', {
                method: 'POST',
                body: JSON.stringify({ skillName, targets }),
            });
            showMessage(msg, data.message || (data.success ? '安装完成' : '安装失败'),
                        data.success ? 'success' : 'error');
            if (data.success) importSkills();
        } catch (e) {
            showMessage(msg, '安装失败: ' + e.message, 'error');
        }
    }

    /* ---------- distribute tab ---------- */

    async function distributeSkills() {
        const targetFolder = $('#targetFolder').value.trim();
        const checkboxes = $$('.distribute-checkbox:checked');

        const msg = $('#distributeMsg');
        msg.style.display = 'block';
        msg.className = 'message show';
        msg.textContent = '正在分发…';

        if (!targetFolder) { showMessage(msg, '请输入目标项目文件夹路径', 'error'); return; }
        if (!checkboxes.length) { showMessage(msg, '请选择至少一个要分发的技能', 'error'); return; }

        const selected = checkboxes.map(cb => state.allSkills[+cb.dataset.idx]);

        try {
            const data = await api('/api/distribute-skills', {
                method: 'POST',
                body: JSON.stringify({ skills: selected, targetFolder }),
            });
            showMessage(msg, data.message || (data.success ? '分发完成' : '分发失败'),
                        data.success ? 'success' : 'error');
        } catch (e) {
            showMessage(msg, '分发失败: ' + e.message, 'error');
        }
    }

    function browseFolder() {
        const input = $('#targetFolder');
        const path = prompt('请输入项目文件夹路径:', input.value || 'D:/');
        if (path) input.value = path;
    }

    /* ---------- side-panel bridge ---------- */

    function openSkillDetail(source, name) {
        state.currentDetail = { source, name };
        window.SkillEditor.open({ source, name });
    }

    function closeSkillDetail() {
        window.SkillEditor.close();
        state.currentDetail = null;
    }

    /* ---------- bootstrap ---------- */

    function bindGlobalEvents() {
        $('#refreshBtn').addEventListener('click', importSkills);
        $('#installHubBtn').addEventListener('click', installSkillhub);
        $('#installBtn').addEventListener('click', installSkill);
        $('#distributeBtn').addEventListener('click', distributeSkills);
        $('#browseFolderBtn').addEventListener('click', browseFolder);
        $('#selectAllBtn').addEventListener('click',
            () => $$('.distribute-checkbox').forEach(cb => (cb.checked = true)));
        $('#deselectAllBtn').addEventListener('click',
            () => $$('.distribute-checkbox').forEach(cb => (cb.checked = false)));
        $('#detailClose').addEventListener('click', closeSkillDetail);
        $('#detailBackdrop').addEventListener('click', closeSkillDetail);
        $$('.detail-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                $$('.detail-tab').forEach(t => t.classList.remove('active'));
                $$('.detail-pane').forEach(p => p.classList.add('hidden'));
                tab.classList.add('active');
                $('#pane' + tab.dataset.pane.charAt(0).toUpperCase() + tab.dataset.pane.slice(1))
                    .classList.remove('hidden');
            });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        setupTabs();
        bindGlobalEvents();
        updateTime();
        setInterval(updateTime, 1000);
        importSkills();
    });

    window.SkillManager = { state, openSkillDetail, closeSkillDetail, importSkills };
})();
