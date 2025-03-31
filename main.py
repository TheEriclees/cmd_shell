import readline
import sys
import shutil
import os
import shlex
import subprocess

tab_state = {"last_text": "", "matches": [], "tab_count": 0}
shell_cmds = ["exit", "echo", "type", "pwd", "cd"]
def auto_complete(text, state):
            global tab_state
            paths = os.getenv("PATH").split(os.pathsep)
            auto = []

            auto.extend(cmd for cmd in shell_cmds if cmd.startswith(text))
           
            for path in paths:
                try:
                    for entry in os.listdir(path):
                        if entry.startswith(text) and os.access(os.path.join(path, entry), os.X_OK):
                            auto.append(entry)
                except FileNotFoundError:
                    pass
            
            if state == 0:
                if tab_state["last_text"] == text:
                    tab_state["tab_count"] += 1
                else:
                    tab_state["tab_count"] = 1
                    tab_state["last_text"] = text
                    tab_state["matches"] = sorted(auto)
                    
            if state < len(tab_state["matches"]):        
                return tab_state["matches"][state] + " " 
                    
            if len(tab_state["matches"]) > 1:
                if tab_state["tab_count"] == 1:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                    return None 
                elif tab_state["tab_count"] == 2:
                    print("\n" + "  ".join(tab_state["matches"]))
                    sys.stdout.write(f"$ {text}")
                    sys.stdout.flush()
                    return None
                
            if state < len(tab_state["matches"]):        
                return tab_state["matches"][state] + " " 
            else:
                return None

def main():
    readline.set_completer(auto_complete)
    readline.parse_and_bind("tab: complete")

    while True:
        home = os.getenv("HOME")
        paths = os.getenv("PATH").split(os.pathsep)
        sys.stdout.write("$ ")
        input_command = input()
        split_input = shlex.split(input_command)
        arg_str = " ".join(split_input[1:])
        shell_builtins = {"exit": "exit", "echo": "echo", "type": "type", "pwd": "pwd", "cd": "cd"}
        command = {}
        
        for path in paths:
            try:
                for entry in os.listdir(path):
                    full_path = os.path.join(path, entry)
                    if entry not in shell_builtins:
                        command.update({entry: full_path})
            except FileNotFoundError:
                pass  

        match split_input:

            case[*cmds, "2>", filename]:
                if filename == None:
                    print("Error: No filename provided for redirection")
                else:
                    try:
                        with open(filename, "w") as error_file:
                            if cmds[0] == "echo":
                                args = shlex.split(" ".join(cmds[1:]))
                                for i in range(len(args)):
                                    if (args[i].startswith("'") and args[i].endswith("'")) or (args[i].startswith('"') and args[i].endswith('"')):
                                        args[i] = args[i][1:-1]
                                print(" ".join(args))
                            else: 
                                result = subprocess.run(cmds, stderr=error_file, stdout=sys.stdout, text=True)
                                if result.returncode != 0:
                                    pass
                    except FileNotFoundError:
                        print(f"Error: Cannot open file '{filename}' for writing")
                    except PermissionError:
                        print(f"Error: Permission denied for file '{filename}'")

            case[*cmds, "2>>", filename]:
                if filename == None:
                    print("Error: No filename provided for redirection")
                else:
                    try:
                        with open(filename, "a") as error_file:
                            if cmds[0] == "echo":
                                args = shlex.split(" ".join(cmds[1:]))
                                for i in range(len(args)):
                                    if (args[i].startswith("'") and args[i].endswith("'")) or (args[i].startswith('"') and args[i].endswith('"')):
                                        args[i] = args[i][1:-1]
                                print(" ".join(args))
                            else: 
                                result = subprocess.run(cmds, stderr=error_file, stdout=sys.stdout, text=True)
                                if result.returncode != 0:
                                    pass
                    except FileNotFoundError:
                        print(f"Error: Cannot open file '{filename}' for appending")
                    except PermissionError:
                        print(f"Error: Permission denied for file '{filename}'")

            case[*cmds, ">", filename] | [*cmds, "1>", filename]: 
                if filename == None:
                    print("Error: No filename provided for redirection")
                else:    
                    try:
                        with open(filename, "w") as output_file:
                            result = subprocess.run(cmds, stdout=output_file, stderr=subprocess.PIPE, text=True)
                            if result.returncode != 0:
                                print(result.stderr.strip())
                    except FileNotFoundError:
                        print(f"Error: Cannot open file '{filename}' for writing")
                    except PermissionError:
                        print(f"Error: Permission denied for file '{filename}'")

            case[*cmds, ">>", filename] | [*cmds, "1>>", filename]: 
                if filename == None:
                    print("Error: No filename provided for redirection")
                else:    
                    try:
                        with open(filename, "a") as output_file:
                            result = subprocess.run(cmds, stdout=output_file, stderr=subprocess.PIPE, text=True)
                            if result.returncode != 0:
                                print(result.stderr.strip())
                    except FileNotFoundError:
                        print(f"Error: Cannot open file '{filename}' for appending")
                    except PermissionError:
                        print(f"Error: Permission denied for file '{filename}'")

            case["cd", *arg]:
                if arg_str == "~":
                    os.chdir(home)
                else:
                    try:
                        os.chdir(arg_str)
                    except FileNotFoundError:
                        print(f"cd: {arg_str}: No such file or directory")

            case ["pwd", *arg]:
                print(os.getcwd())

            case ["exit", "0"]:
                sys.exit(0)

            case ["echo", *arg]:
                args = shlex.split(input_command[5:])
                for i in range(len(args)):
                    if (args[i].startswith("'") and args[i].endswith("'")) or (args[i].startswith('"') and args[i].endswith('"')):
                        args[i] = args[i][1:-1]
                print(" ".join(args))

            case ["type", *arg]:
                if arg_str in shell_cmds:
                    print(f"{arg_str} is a shell builtin")
                elif path := shutil.which(arg_str):
                    print(f"{arg_str} is {path}")
                else:
                    print(f"{arg_str}: not found")

            case [cmd, *arg]:
                if cmd not in command and cmd not in shell_builtins:
                    try:
                        if shutil.which(cmd):
                            quote_cmd = shlex.quote(cmd)
                            quote_args = [shlex.quote(a) for a in arg]
                            os.system(" ".join([quote_cmd] + quote_args))
                        else:
                            print(f"{input_command}: command not found")
                    except Exception as e:
                        print(f"Error executing command: {e}")
                        
                elif cmd in command:
                    quote_cmd = shlex.quote(cmd)
                    quote_args = [shlex.quote(a) for a in arg]
                    os.system(" ".join([quote_cmd] + quote_args))

if __name__ == "__main__":
    main()