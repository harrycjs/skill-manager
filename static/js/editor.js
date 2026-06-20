// SkillEditor — owns the side panel: skill metadata, file tree, and CodeMirror view.
// Exposed as window.SkillEditor so app.js can drive the panel.

(function () {
    'use strict';

    const EXT_TO_MODE = {
        md: 'markdown',
        markdown: 'markdown',
        py: 'python',
        js: 'javascript',
        ts: 'javascript',
        jsx: 'javascript',
        tsx: 'javascript',
        json: 'json',
        yaml: 'yaml',
        yml: 'yaml',
        sh: 'shell',
        bash: 'shell',
        toml: 'toml',
        css: 'css',
        html: 'htmlmixed',
        htm: 'htmlmixed',
        xml: 'xml',
    };

    const EDITABLE_EXTS = new Set([
        'md', 'markdown', 'py', 'js', 'ts', 'jsx', 'tsx',
        'json', 'yaml', 'yml', 'sh', 'bash', 'toml',
        'css', 'html', 'htm', 'xml', 'txt',
    ]);

    const panel = () => document.getElementById('skillDetail');
    const backdrop = () => document.getElementById('detailBackdrop');
    const tree = () => document.getElementById('fileTree');
    const viewer = () => document.getElementById('fileViewer');
    const viewerBody = () => document.getElementById('viewerBody');
    const viewerPath = () => document.getElementById('viewerPath');

    let current = null;       // {source, name}
    let entries = [];         // file tree entries
    let cmInstance = null;    // CodeMirror instance when editing

    /* ---------- DOM helpers ---------- */

    function $(id) {
        return document.getElementById(id);
    }

    function escapeHtml(text) {
        return String(text || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function toast(msg, kind = 'success') {
        const el = document.createElement('div');
        el.className = 'toast ' + kind;
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2400);
    }

    function formatBytes(n) {
        if (!n) return '0 B';
        const u = ['B', 'KB', 'MB', 'GB'];
        let i = 0;
        while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
        return n.toFixed(n < 10 ? 1 : 0) + ' ' + u[i];
    }

    function formatTime(ts) {
        if (!ts) return '—';
        return new Date(ts * 1000).toLocaleString();
    }

    /* ---------- panel lifecycle ---------- */

    async function open({ source, name }) {
        current = { source, name };
        panel().classList.remove('hidden');
        backdrop().classList.remove('hidden');
        await loadDetail();
    }

    function close() {
        destroyEditor();
        panel().classList.add('hidden');
        backdrop().classList.add('hidden');
        current = null;
        entries = [];
    }

    /* ---------- detail + tree loading ---------- */

    async function loadDetail() {
        const { source, name } = current;
        $('detailName').textContent = name;

        try {
            const detail = await fetch(
                `/api/skills/${encodeURIComponent(source)}/${encodeURIComponent(name)}`
            ).then(r => r.json());

            if (detail.error) {
                $('detailMeta').innerHTML =
                    '<span class="pill" style="color:var(--error)">' + escapeHtml(detail.error) + '</span>';
                $('detailReadme').textContent = '加载失败';
                tree().innerHTML = '';
                return;
            }

            $('detailMeta').innerHTML = `
                <span class="pill">source: ${escapeHtml(source)}</span>
                <span class="pill">${detail.file_count} 文件</span>
                <span class="pill">${formatBytes(detail.total_size)}</span>
                <span class="pill">最近更新 ${formatTime(detail.last_mtime)}</span>
            `;

            if (detail.has_skill_md && window.marked) {
                $('detailReadme').innerHTML = window.marked.parse(detail.skill_md || '');
            } else if (detail.has_skill_md) {
                $('detailReadme').textContent = detail.skill_md || '';
            } else {
                $('detailReadme').innerHTML =
                    '<span style="color:var(--text-muted)">该技能没有 SKILL.md 文件</span>';
            }

            await loadTree();
        } catch (e) {
            $('detailMeta').innerHTML =
                '<span class="pill" style="color:var(--error)">' + escapeHtml(e.message) + '</span>';
        }
    }

    async function loadTree() {
        const { source, name } = current;
        try {
            const data = await fetch(
                `/api/skills/${encodeURIComponent(source)}/${encodeURIComponent(name)}/files`
            ).then(r => r.json());

            if (data.error) {
                tree().innerHTML = '<div class="message error show">' + escapeHtml(data.error) + '</div>';
                entries = [];
                return;
            }
            entries = data.entries || [];
            renderTree();
        } catch (e) {
            tree().innerHTML = '<div class="message error show">加载文件树失败: ' + escapeHtml(e.message) + '</div>';
        }
    }

    function renderTree() {
        const filter = ($('fileSearch').value || '').toLowerCase();
        const visible = entries.filter(e => !filter || e.path.toLowerCase().includes(filter));

        if (!visible.length) {
            tree().innerHTML = '<div style="color:var(--text-muted);padding:12px;">无匹配文件</div>';
            return;
        }

        tree().innerHTML = visible.map(e => {
            const isDir = e.type === 'dir';
            const icon = isDir ? '▸' : '·';
            const ext = isDir ? '' : (e.path.split('.').pop() || '').toLowerCase();
            const editable = !isDir && EDITABLE_EXTS.has(ext);
            const disabledCls = (!isDir && !editable) ? ' disabled' : '';
            const size = isDir ? '' : formatBytes(e.size);
            return `
                <div class="tree-row${disabledCls}" data-path="${escapeHtml(e.path)}" data-type="${e.type}">
                    <span class="icon">${icon}</span>
                    <span class="name">${escapeHtml(e.name)}</span>
                    <span class="meta">${size}</span>
                </div>
            `;
        }).join('');

        $$('#fileTree .tree-row').forEach(row => {
            row.addEventListener('click', () => {
                if (row.dataset.type === 'dir') return;
                if (row.classList.contains('disabled')) {
                    toast('该文件类型不允许在线编辑', 'error');
                    return;
                }
                openFile(row.dataset.path);
            });
        });
    }

    function $$(sel, root = document) {
        return Array.from(root.querySelectorAll(sel));
    }

    /* ---------- file viewer / editor ---------- */

    async function openFile(relPath) {
        destroyEditor();
        const { source, name } = current;
        viewer().classList.remove('hidden');
        viewerPath().textContent = relPath;
        viewerBody().innerHTML = '<div class="loading">加载中…</div>';

        try {
            const data = await fetch(
                `/api/skills/${encodeURIComponent(source)}/${encodeURIComponent(name)}/file?path=${encodeURIComponent(relPath)}`
            ).then(r => r.json());

            if (data.error) {
                viewerBody().innerHTML =
                    '<div class="message error show">' + escapeHtml(data.error) + '</div>';
                $('viewerEdit').classList.add('hidden');
                return;
            }

            const ext = (relPath.split('.').pop() || '').toLowerCase();
            const mode = EXT_TO_MODE[ext];

            if (data.editable && mode && window.CodeMirror) {
                viewerBody().innerHTML = '';
                cmInstance = window.CodeMirror(viewerBody(), {
                    value: data.content,
                    mode: mode,
                    theme: 'material-darker',
                    lineNumbers: true,
                    lineWrapping: true,
                    indentUnit: 4,
                });
                $('viewerEdit').textContent = '保存';
                $('viewerEdit').onclick = () => saveFile(relPath);
                $('viewerEdit').classList.remove('hidden');
                setTimeout(() => cmInstance && cmInstance.refresh(), 50);
            } else {
                viewerBody().innerHTML =
                    '<pre>' + escapeHtml(data.content) + '</pre>';
                $('viewerEdit').classList.add('hidden');
            }
        } catch (e) {
            viewerBody().innerHTML =
                '<div class="message error show">' + escapeHtml(e.message) + '</div>';
        }
    }

    function closeFileViewer() {
        destroyEditor();
        viewer().classList.add('hidden');
        viewerBody().innerHTML = '';
        viewerPath().textContent = '';
    }

    function destroyEditor() {
        if (cmInstance) {
            try { cmInstance.toTextArea(); } catch (_) { /* ignore */ }
            cmInstance = null;
        }
    }

    async function saveFile(relPath) {
        if (!cmInstance) return;
        const { source, name } = current;
        const content = cmInstance.getValue();
        try {
            const res = await fetch(
                `/api/skills/${encodeURIComponent(source)}/${encodeURIComponent(name)}/file`,
                {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: relPath, content }),
                }
            );
            const data = await res.json();
            if (!res.ok || data.error) {
                toast('保存失败: ' + (data.error || `HTTP ${res.status}`), 'error');
                return;
            }
            toast(`已保存 (${formatBytes(data.size)})`, 'success');
            // If we edited SKILL.md, refresh the rendered panel too.
            if (relPath.endsWith('SKILL.md')) loadDetail();
            else loadTree();
        } catch (e) {
            toast('保存失败: ' + e.message, 'error');
        }
    }

    /* ---------- detail-tab switching ---------- */

    // The tab buttons live in app.js's binding block; ensure the Files tab
    // re-renders if the user re-enters while filter text is still typed.
    document.addEventListener('DOMContentLoaded', () => {
        const search = document.getElementById('fileSearch');
        if (search) search.addEventListener('input', renderTree);
        const refresh = document.getElementById('refreshTree');
        if (refresh) refresh.addEventListener('click', () => loadTree());
        const viewerClose = document.getElementById('viewerClose');
        if (viewerClose) viewerClose.addEventListener('click', closeFileViewer);
    });

    window.SkillEditor = { open, close, loadTree };
})();
