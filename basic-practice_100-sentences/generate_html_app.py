import re
import datetime
import json
import os

def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by "### Q" to get chunks, ignore preamble
    chunks = re.split(r'### Q(\d+)', content)
    
    questions = []
    
    # chunks[0] is preamble.
    # chunks[1] is num for Q1, chunks[2] is content for Q1, and so on.
    for i in range(1, len(chunks), 2):
        q_num = int(chunks[i])
        q_content = chunks[i+1]
        
        # Extract Chinese Prompt
        # Looking for **中文题目**:\n> (.*)
        chinese_match = re.search(r'\*\*中文题目\*\*:\s*\n>\s*(.*)', q_content)
        chinese_text = chinese_match.group(1).strip() if chinese_match else "N/A"
        
        # Extract Hints HTML structure
        # We can just extract everything between <details> and </details>
        hints_match = re.search(r'(<details>.*?</details>)', q_content, re.DOTALL)
        hints_html = hints_match.group(1).strip() if hints_match else ""
        
        questions.append({
            "id": q_num,
            "chinese": chinese_text,
            "hints": hints_html
        })
        
    return questions

def generate_html(questions, output_path):
    # Split into sets
    sets = []
    chunk_size = 20
    for i in range(0, len(questions), chunk_size):
        subset = questions[i:i+chunk_size]
        start = subset[0]['id']
        end = subset[-1]['id']
        sets.append({
            "name": f"Set {len(sets)+1} (Q{start:02d}-Q{end:02d})",
            "start": start,
            "end": end,
            "questions": subset
        })
        
    # JSON data for JS
    json_data = json.dumps(sets, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IELTS 100 Sentences Practice</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --surface: #ffffff;
            --text: #1e293b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
            padding-bottom: 80px; /* Space for footer */
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .controls {{
            background: var(--surface);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            position: sticky;
            top: 10px;
            z-index: 100;
        }}
        select {{
            padding: 8px 12px;
            font-size: 16px;
            border-radius: 4px;
            border: 1px solid #cbd5e1;
        }}
        .question-card {{
            background: var(--surface);
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        .q-header {{
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-bottom: 15px;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .q-num {{
            color: var(--primary);
        }}
        .chinese-text {{
            font-size: 1.1em;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #e2e8f0;
        }}
        textarea {{
            width: 100%;
            height: 80px;
            padding: 10px;
            margin-top: 15px;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            font-family: inherit;
            resize: vertical;
            box-sizing: border-box; 
        }}
        textarea:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
        }}
        details {{
            background-color: #f1f5f9;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            cursor: pointer;
        }}
        summary {{
            font-weight: 500;
            color: #64748b;
        }}
        .fab-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--surface);
            padding: 15px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
            display: flex;
            justify-content: center;
            border-top: 1px solid #e2e8f0;
        }}
        .btn {{
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .btn:hover {{
            background-color: #1d4ed8;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>IELTS Writing 100 Sentences</h1>
    </header>

    <div class="controls">
        <label for="set-select">Choose Practice Set: </label>
        <select id="set-select" onchange="renderQuestions()">
            <!-- Options populated by JS -->
        </select>
    </div>

    <div id="questions-container">
        <!-- Questions populated by JS -->
    </div>
</div>

<div class="fab-footer">
    <button class="btn" onclick="exportMarkdown()">📥 Export Answers to Markdown</button>
</div>

<script>
    const practiceSets = {json_data};
    let currentSetIndex = 0;

    function init() {{
        const select = document.getElementById('set-select');
        practiceSets.forEach((set, index) => {{
            const option = document.createElement('option');
            option.value = index;
            option.text = set.name;
            select.appendChild(option);
        }});
        renderQuestions();
    }}

    function renderQuestions() {{
        const select = document.getElementById('set-select');
        currentSetIndex = parseInt(select.value);
        const set = practiceSets[currentSetIndex];
        const container = document.getElementById('questions-container');
        
        container.innerHTML = '';
        
        set.questions.forEach(q => {{
            const card = document.createElement('div');
            card.className = 'question-card';
            card.innerHTML = `
                <div class="q-header">
                    <span class="q-num">Q${{q.id}}</span>
                </div>
                <div class="chinese-text">
                    ${{q.chinese}}
                </div>
                 <div class="hints-area">
                    ${{q.hints}}
                </div>
                <textarea id="answer-${{q.id}}" placeholder="Type your English translation here..."></textarea>
            `;
            container.appendChild(card);
        }});
        
        // Restore answers if exists in local storage? (Optional, but good for UX. Let's keep it simple for now)
        window.scrollTo(0,0);
    }}

    function formatDate(date) {{
        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        return `${{yyyy}}${{mm}}${{dd}}`; // As per user file usage '20251221'
    }}

    function exportMarkdown() {{
        const set = practiceSets[currentSetIndex];
        const now = new Date();
        const dateStr = formatDate(now);
        
        // Format: 2025-12-21_Set1_Q01-Q20.md  (User request format)
        // Wait, user used 20251221 in file creation, but requested 2025-12-21 in prompt.
        // I will follow the explicit request in the prompt: 2025-12-21_Set1_Q01-Q20.md
        
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const filenameDate = `${{yyyy}}-${{mm}}-${{dd}}`;
        
        const setNum = currentSetIndex + 1;
        const startQ = String(set.start).padStart(2, '0');
        const endQ = String(set.end).padStart(2, '0');
        
        const filename = `${{filenameDate}}_Set${{setNum}}_Q${{startQ}}-Q${{endQ}}.md`;
        
        let content = `# IELTS Writing Practice Set ${{setNum}} (Q${{startQ}}-Q${{endQ}})\\n\\n> **Date**: ${{filenameDate}}\\n\\n`;
        
        set.questions.forEach(q => {{
            const answer = document.getElementById(`answer-${{q.id}}`).value;
            content += `### Q${{q.id}}\\n`;
            content += `**中文题目**:\\n> ${{q.chinese}}\\n\\n`;
            content += `**词伙提示 (Hints)**:\\n${{q.hints}}\\n\\n`;
            content += `**你的回答 (Your Answer)**:\\n> ${{answer}}\\n\\n`;
            content += `---\\n\\n`;
        }});
        
        download(filename, content);
    }}

    function download(filename, text) {{
        var element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);
    }}

    window.onload = init;
</script>

</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    md_path = "/Users/macbookair/vscode-workspace/ielts-assistant/basic-practice_100-sentences/ielts_practice_100.md"
    html_path = "/Users/macbookair/vscode-workspace/ielts-assistant/basic-practice_100-sentences/ielts_practice_app.html"
    questions = parse_markdown(md_path)
    generate_html(questions, html_path)
