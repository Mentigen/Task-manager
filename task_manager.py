import sublime
import sublime_plugin
import re


class TodoManagerCommand(sublime_plugin.TextCommand):
    # Ключевые слова и их приоритеты из настроек
    TASK_KEYWORDS = sublime.load_settings("todo_manager.sublime-settings").get("keywords")

    # Описания приоритетов
    PRIORITY_DESCRIPTIONS = {
        1: "Critical",
        2: "High Priority",
        3: "Medium Priority",
        4: "Low Priority",
        5: "Minor"
    }

    def run(self, edit):
        # Собираем задачи из текущего файла и всех открытых файлов
        all_tasks = self.collect_all_tasks()

        if all_tasks:
            # Отображаем фильтр задач
            self.display_filter_options(all_tasks)
        else:
            sublime.message_dialog("No tasks found.")

    def collect_all_tasks(self):
        """Собираем задачи из всех открытых файлов."""
        tasks = []
        for window in sublime.windows():
            for view in window.views():
                if view.file_name():  # Только для открытых файлов
                    content = view.substr(sublime.Region(0, view.size()))
                    tasks.extend(self.find_tasks(content, view))
        return tasks

    def find_tasks(self, content, view):
        """Ищем задачи с ключевыми словами в тексте."""
        tasks = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            for keyword, default_priority in self.TASK_KEYWORDS.items():
                if keyword in line:
                    priority = self.extract_priority(line, default_priority)
                    cleaned_line = self.clean_priority_from_text(line)
                    tasks.append({
                        "view": view,
                        "line_number": line_number,
                        "text": cleaned_line.strip(),
                        "priority": priority
                    })
        return sorted(tasks, key=lambda task: task["priority"])

    def extract_priority(self, text, default_priority):
        """Извлекаем приоритет из строки."""
        match = re.search(r"\[(\d+)\]", text)
        if match:
            return int(match.group(1))
        return default_priority

    def clean_priority_from_text(self, text):
        """Удаляем приоритет из текста задачи."""
        return re.sub(r"\s*\[\d+\]", "", text)

    def display_filter_options(self, tasks):
        """Отображаем фильтр задач."""
        keywords = list(self.TASK_KEYWORDS.keys())
        keywords.append("All")  # Опция для отображения всех задач
        self.view.window().show_quick_panel(
            keywords,
            lambda index: self.filter_and_show_tasks(tasks, keywords[index]) if index != -1 else None
        )

    def filter_and_show_tasks(self, tasks, filter_keyword):
        """Фильтруем задачи по ключевому слову и отображаем их."""
        if filter_keyword != "All":
            tasks = [task for task in tasks if filter_keyword in task["text"]]
        task_list = [
            f"{task['line_number']} ({self.priority_to_description(task['priority'])}): {task['text']}"
            for task in tasks
        ]
        self.view.window().show_quick_panel(
            task_list,
            lambda index: self.goto_task(tasks, index) if index != -1 else None
        )

    def priority_to_description(self, priority):
        """Преобразует числовой приоритет в текстовое описание."""
        return self.PRIORITY_DESCRIPTIONS.get(priority, "Unknown priority")

    def goto_task(self, tasks, index):
        """Переход к строке с задачей."""
        if index < 0:
            return
        task = tasks[index]
        view = task["view"]
        point = view.text_point(task["line_number"] - 1, 0)
        view.sel().clear()
        view.sel().add(sublime.Region(point))
        view.show_at_center(point)
