import logging
import os
import platform
import subprocess
import sys

logger = logging.getLogger(__name__)

TASK_NAME = "DeadlinerDailySync"


def get_sync_command() -> str:
    """Return the exact command string to execute sync-all."""
    # Use the active python binary with -m deadliner sync-all
    py_exe = sys.executable
    return f'"{py_exe}" -m deadliner sync-all'


def enable_schedule(time_str: str = "08:00") -> tuple[bool, str]:
    """Enable daily 24h auto-sync in OS scheduler.

    Args:
        time_str: Time in HH:MM format (24h clock, e.g. "08:00").

    Returns:
        (success, message)
    """
    cmd_str = get_sync_command()
    system = platform.system().lower()

    if system == "windows":
        try:
            # schtasks /Create /SC DAILY /TN "DeadlinerDailySync" /TR "..." /ST 08:00 /F
            res = subprocess.run(
                [
                    "schtasks",
                    "/Create",
                    "/SC",
                    "DAILY",
                    "/TN",
                    TASK_NAME,
                    "/TR",
                    cmd_str,
                    "/ST",
                    time_str,
                    "/F",
                ],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return True, f"Daily auto-sync scheduled successfully for {time_str} every day."
            return False, f"Failed to create Windows scheduled task: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Error creating Windows scheduled task: {e}"

    else:
        # Linux / macOS crontab
        try:
            hour, minute = time_str.split(":")
            cron_time = f"{int(minute)} {int(hour)} * * *"
            cron_line = f"{cron_time} {cmd_str} # {TASK_NAME}\n"

            curr_cron = ""
            read_res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if read_res.returncode == 0:
                curr_cron = read_res.stdout

            # Filter out previous Deadliner task
            new_lines = [line for line in curr_cron.splitlines() if TASK_NAME not in line]
            new_lines.append(cron_line.strip())
            new_cron_text = "\n".join(new_lines) + "\n"

            write_res = subprocess.run(["crontab", "-"], input=new_cron_text, text=True, capture_output=True)
            if write_res.returncode == 0:
                return True, f"Daily auto-sync scheduled via crontab for {time_str} every day."
            return False, f"Failed to update crontab: {write_res.stderr.strip()}"
        except Exception as e:
            return False, f"Error setting up crontab: {e}"


def disable_schedule() -> tuple[bool, str]:
    """Disable/remove the daily auto-sync task from OS scheduler."""
    system = platform.system().lower()

    if system == "windows":
        try:
            res = subprocess.run(
                ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return True, "Daily auto-sync has been disabled."
            if "cannot find" in res.stderr.lower() or "not found" in res.stderr.lower():
                return True, "Daily auto-sync is already disabled (task not found)."
            return False, f"Failed to remove Windows task: {res.stderr.strip()}"
        except Exception as e:
            return False, f"Error removing task: {e}"

    else:
        try:
            read_res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if read_res.returncode != 0:
                return True, "Daily auto-sync is already disabled."

            curr_cron = read_res.stdout
            new_lines = [line for line in curr_cron.splitlines() if TASK_NAME not in line]
            new_cron_text = "\n".join(new_lines).strip()
            if new_cron_text:
                new_cron_text += "\n"

            write_res = subprocess.run(["crontab", "-"], input=new_cron_text, text=True, capture_output=True)
            if write_res.returncode == 0:
                return True, "Daily auto-sync has been disabled."
            return False, f"Failed to update crontab: {write_res.stderr.strip()}"
        except Exception as e:
            return False, f"Error updating crontab: {e}"


def get_schedule_status() -> dict:
    """Return status dictionary of the scheduled task."""
    system = platform.system().lower()

    if system == "windows":
        try:
            res = subprocess.run(
                ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                return {"enabled": False, "details": "No scheduled task found."}

            output = res.stdout
            details = {}
            for line in output.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    k_clean = k.strip()
                    v_clean = v.strip()
                    if k_clean in (
                        "TaskName",
                        "Next Run Time",
                        "Status",
                        "Last Run Time",
                        "Last Result",
                        "Schedule Type",
                        "Start Time",
                    ):
                        details[k_clean] = v_clean

            return {
                "enabled": True,
                "next_run": details.get("Next Run Time", "Unknown"),
                "status": details.get("Status", "Ready"),
                "start_time": details.get("Start Time", ""),
                "details": details,
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    else:
        try:
            read_res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if read_res.returncode != 0:
                return {"enabled": False, "details": "No crontab entries found."}

            found_line = ""
            for line in read_res.stdout.splitlines():
                if TASK_NAME in line:
                    found_line = line
                    break

            if found_line:
                return {"enabled": True, "cron_entry": found_line}
            return {"enabled": False, "details": "No Deadliner task in crontab."}
        except Exception as e:
            return {"enabled": False, "error": str(e)}
