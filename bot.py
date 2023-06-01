import tempfile
from uuid import uuid4

from botcity.maestro import BotMaestroSDK, AutomationTaskFinishStatus, Column
from datetime import datetime
from botcity.plugins.recorder import BotRecorderPlugin
from botcity.web import WebBot, Browser, By
from webdriver_manager.firefox import GeckoDriverManager


class Bot:
    def __init__(self):
        self.maestro = BotMaestroSDK.from_sys_args()
        self.maestro.RAISE_NOT_CONNECTED = False
        self.execution = self.maestro.get_execution()
        self.parameters = self.maestro.get_task(task_id=self.execution.task_id).parameters
        self.tmp_folder = tempfile.TemporaryDirectory()
        self.filepath = f"{self.tmp_folder.name}/execution_bot_linkedin_{self.execution.task_id}.avi"
        self.filepath = f"{self.tmp_folder.name}/meetup_management_automation_123.avi"
        self.screenshot_filepath = f"{self.tmp_folder.name}/error.png"
        self.bot = self._configure_browser()

    def _configure_browser(self) -> WebBot:
        bot = WebBot()
        bot.browser = Browser.FIREFOX
        driver_path = GeckoDriverManager(path=self.tmp_folder.name).install()
        bot.driver_path = driver_path
        bot.headless = False
        return bot

    def create_log(self):
        try:
            columns = [
                Column(name="Date/Time", label='timestamp', width=300),
                Column(name="Id", label='id', width=200),
                Column(name="Status", label='status', width=100),
                Column(name="Message", label='message', width=300),
            ]
            self.maestro.new_log(
                activity_label="meetup-management-automation",
                columns=columns
            )
        except Exception as error:
            print(error)

    def start(self):
        self.bot.start_browser()
        recorder = BotRecorderPlugin(bot=self.bot, output_file=self.filepath)
        message = "Execution took place without technical failures " \
                  "(search failures could be seen in the errors and alerts section.)"
        status = AutomationTaskFinishStatus.SUCCESS
        recorder.start()
        try:
            self.create_log()
            self.bot.navigate_to("https://botcity.dev")
            if self.execution.parameters.get("execute_error", "") == "yes":
                element = self.bot.find_element(selector="/html/body/div[4]/div/div/div/div[1]/div/div[2]/a", by=By.XPATH)
                if not element:
                    raise RuntimeError("Could not find the element.")
            self.maestro.new_log_entry(
                activity_label="meetup-management-automation",
                values={
                    "id": str(uuid4()),
                    "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M"),
                    "status": "SUCCESS",
                    "message": "O processo foi concluído com sucesso"
                }
            )
            self.bot.sleep(5000)
        except Exception as error:
            message = "Error executing the automation, please check the errors section"
            status = AutomationTaskFinishStatus.FAILED
            self.bot.screenshot(self.screenshot_filepath)
            recorder.stop()
            self.maestro.error(
                task_id=self.execution.task_id,
                screenshot=self.screenshot_filepath,
                exception=error,
                attachments=[self.filepath]
            )
            self.maestro.new_log_entry(
                activity_label="meetup-management-automation",
                values={
                    "id": str(uuid4()),
                    "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M"),
                    "status": "ERROR",
                    "message": "O processo foi concluído com erro técnico."
                }
            )
        finally:
            if recorder.state != "stopped":
                recorder.stop()
            self.bot.stop_browser()
            self.maestro.finish_task(
                task_id=self.execution.task_id,
                message=message,
                status=status
            )
            self.maestro.post_artifact(
                task_id=self.execution.task_id,
                artifact_name="result",
                filepath="./result.pdf"
            )
            self.tmp_folder.cleanup()


if __name__ == '__main__':
    bot = Bot()
    bot.start()
