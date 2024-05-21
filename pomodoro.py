#!/usr/bin/env python

import prompt_toolkit as prompt
import time, datetime, playsound, os
import pandas as pd

basedir = os.path.expanduser('~/pomodoro')

if not os.path.isdir(basedir):
    os.mkdir(basedir)

logfile = f'{basedir}/work.log'
soundfile = f'{basedir}/listen.mp3'

stages = ['🮣', '🮦', '🮪', '🮮']
# stages = ['🬃', '🬅', '🬍', '🬎']

session_duration = 25 # minutes
break_duration = 5    # minutes

day_starts_at = 6 # hours

def timer(duration):
    """
    Start a timer for the given duration.

    Args:
        duration (int): The duration of the timer in seconds.

    Returns:
        float: The elapsed time in seconds.
    """
    start, elapsed = time.time(), 0
    try:
        while elapsed < duration:
            elapsed = time.time() - start
            print(f'{float_to_int(duration - elapsed)//60:02}:{float_to_int(duration - elapsed)%60:02}', end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        print('\rinterrupted')
    else:
        notify()
    finally:
        return elapsed

def notify():
    """
    Play a notification sound.
    """
    playsound.playsound(soundfile)

def int_to_ticks(num):
    """
    Convert an integer to a string representation of ticks.

    Args:
        num (int): The integer to convert.

    Returns:
        str: The string representation of ticks.
    """
    return ' '.join((float_to_int(num) // 4)*[stages[-1]]) + ' ' + (stages[float_to_int(num) % 4 - 1] if float_to_int(num) % 4 > 0 else '')

def float_to_int(num):
    """
    Convert a float to an integer. If the float is close to the next integer, round up.

    Args:
        num (float): The float to convert.

    Returns:
        int: The integer representation of the float.
    """
    return int(num) + 1 if abs(num - int(num) - 1) < 1e-3 else int(num)

def log_work(project, duration, work_session = None):
    """
    Log work to the log file.

    Args:
        project (str): The project name.
        duration (int): The duration of the work in seconds.
    """
    if work_session is not None:
        if project not in work_session:
            work_session[project] = 0
        work_session[project] += duration
    with open(logfile, 'a') as f:
        f.write(f'{time.time() - duration:.0f}\t{project}\t{duration:.0f}\n')

def print_session(s):
    """
    Print the session summary.

    Args:
        s (dict): The session summary.
    """
    print('    '.join([f'{p} {int_to_ticks(s[p]/60/session_duration)}' for p in s if s[p] > 0.8*session_duration*60]))

def main():
    """
    Main function to run the Pomodoro timer.
    """

    if not os.path.exists(logfile):
        with open(logfile, 'w') as f:
            f.write('start\tproject\tduration\n')

    log = pd.read_csv(logfile, sep='\s+')

    work_session = {}
    today = time.mktime(datetime.date.today().timetuple()) + day_starts_at*3600
    for row in log[log.start > today].itertuples():
        if row.project not in work_session:
            work_session[row.project] = 0
        work_session[row.project] += row.duration

    projects = set(log.project)

    session = prompt.PromptSession()

    print_session(work_session)

    while True:
        try:
            projects_completer = prompt.completion.NestedCompleter.from_nested_dict({
                'work': projects,
                'add': projects,
                'list': {
                    'projects': None,
                    'today': None
                    },
                'quit': None,
                })
            
            args = session.prompt('pomodoro ~ ', completer=projects_completer).split()

            if not args:
                args = ['list']

            if args[0] == 'quit':
                break

            if args[0] == 'list':
                if len(args) > 2:
                    print('invalid argument')
                    continue
                if len(args) <= 1:
                    args = ['list', '0']
                
                if args[1] == 'projects':
                    print('\n'.join(projects))
                    continue
                if args[1] == 'today':
                    args[1] = 0
                try:
                    day = time.mktime(datetime.date.today().timetuple()) + day_starts_at*3600 - int(args[1])*86400 if len(args) > 1 else today
                    if int(args[1]) > 0:
                        print(datetime.datetime.fromtimestamp(day).strftime('%Y-%m-%d'))
                    else:
                        print('today')
                except ValueError:
                    print('invalid argument')
                    continue
                
                s = {}
                for row in log[(log.start > day) * (log.start < day + 86400)].itertuples():
                    if row.project not in s:
                        s[row.project] = 0
                    s[row.project] += row.duration
                print_session(s)
                continue

            if args[0] == 'add':
                for a in args[1:]:
                    projects.add(a)
                    log_work(a, session_duration*60, work_session=work_session)
                print_session(work_session)
                continue

            if args[0] == 'work' and len(args) > 1:
                project = args[1]
                projects.add(project)
                elapsed = timer(session_duration*60)
                if elapsed > 10:
                    log_work(project, elapsed, work_session=work_session)
                print('break')
                timer(break_duration*60)
                print_session(work_session)
                continue

            print('unknown command')

        except (EOFError, KeyboardInterrupt):
            break

if __name__ == '__main__':
    main()
 
