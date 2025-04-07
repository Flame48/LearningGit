import os
import re
import subprocess
import json

class LessonManager:
    
    lessons: list
    
    def __init__(self):
        with open('./.availablelessons', 'r') as f:
            self.lessons = json.load(f)
    
    def run(self) -> None:
        print("Welcome to LearningGit!")
        
        while True:
            print("Which Activity would you like to do?")
            for i, l in enumerate(self.lessons, 1):
                print(f'{i}. {l["title"]} - {l["difficulty"]}')
            print("[Q]. Quit")
            ch: str = input("> ").strip().lower()
            if (ch == 'q'):
                print("Quitting")
                break
            if (not ch.isnumeric()):
                print("Please enter the activity number.")
                continue
            ch: int = int(ch)
            if (ch<1) or (ch>len(self.lessons)):
                print(f"That activity is out of range. Please enter a number between [1 - {len(self.lessons)}] to select the corresponding activity.")
                continue
            
            selected_lesson = self.lessons[ch-1]
            
            cwd = os.getcwd()
            try:
                subprocess.run(
                    f"git clone {selected_lesson['url']} {selected_lesson['to']}", shell=True, stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as e:
                print(f"Error loading activity")
                continue
            
            for cmd in selected_lesson['setup_commands']:
                subprocess.run(cmd, shell=True, stderr=subprocess.STDOUT)
            
            runner = LessonRunner(selected_lesson)
            runner.run()
            
            os.chdir(cwd)
            subprocess.run(f"rm -rf {selected_lesson['to']}", shell=True, stderr=subprocess.STDOUT)
            for cmd in selected_lesson['cleanup_commands']:
                subprocess.run(cmd, shell=True, stderr=subprocess.STDOUT)

class LessonRunner:
    def __init__(self, lesson):
        self.title = lesson['title']
        self.difficulty = lesson['difficulty']
        
        self.lesson_path = os.path.abspath(lesson['to'])
        with open(os.path.join(self.lesson_path, '.lessonplan'), "r") as f:
            self.steps = json.load(f)
        os.chdir(self.lesson_path)    
        
        self.step_index = 0
        self.command_history = []
        self.neutral_prefixes = ["ls", "cat", "git status", "git log"]
        self.expected_command = lambda step: step["expected_command"]
        self.allow_equivalents = lambda step: step.get("allow_equivalents", [])

    def run(self):
        to_print = f"Starting Lesson \"{self.title}\""
        print(to_print, '-'*len(to_print), sep='\n')
        
        while self.step_index < len(self.steps):
            step = self.steps[self.step_index]
            print(f"\nStep {self.step_index + 1}:\n{step['explanation']}")

            while True:
                user_input = input("> ").strip()
                self.command_history.append(user_input)

                if user_input.startswith("!"):
                    self.handle_app_command(user_input, step)
                    continue

                if self.is_expected_command(user_input, step):
                    if ('end' in step) and step['end']:
                        return
                    success = self.run_shell(user_input)
                    if not success:
                        continue
                    print("Correct!")
                    self.step_index += 1
                    break

                elif self.is_neutral_command(user_input):
                    self.run_shell(user_input)

                else:
                    print("That's not the command we're looking for.")
                    print("Type !hint if you're stuck.")

        print("\n Lesson complete! Great job.")

    def handle_app_command(self, user_input, step):
        if user_input == "!hint":
            print(f"Hint: {step['hint']}")
        elif user_input == "!history":
            print("Command History:")
            for cmd in self.command_history:
                print(f"  {cmd}")
        elif user_input == "!exit":
            print("Exiting.")
            exit()
        else:
            print("Unknown application command.")

    def is_expected_command(self, cmd, step) -> bool:
        pattern = step["expected_command"]
        if re.fullmatch(pattern, cmd) is not None:
            return True
        if ("allow_equivalents" in step):
            for equiv in step['allow_equivalents']:
                if re.fullmatch(equiv, cmd) is not None:
                    return True
        return False

    def is_neutral_command(self, cmd: str) -> bool:
        return any(cmd.startswith(prefix) for prefix in self.neutral_prefixes)

    def run_shell(self, cmd: str) -> bool:
        try:
            output = subprocess.check_output(
                cmd, shell=True, cwd=self.lesson_path, stderr=subprocess.STDOUT
            )
            print(output.decode())
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!!] Command error:\n{e.output.decode()}")
            return False

if __name__ == '__main__':
    print("initiating startup...")
    LessonManager().run()