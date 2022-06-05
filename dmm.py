import settings
import shutil
import os
import time
from loguru import logger

def patch_dmm():
    resources_path = os.path.join(settings.get("dmm_path"), "resources")
    if os.path.isdir(resources_path):
        if os.path.isfile(os.path.join(resources_path, "app.asar.org")):
            logger.info("Found remnants of a patch. Reverting.")
            unpatch_dmm()

        logger.info("Patching DMM")
        cwd_before = os.getcwd()
        os.chdir(resources_path)

        logger.info("Backing up app.asar.")
        shutil.copy("app.asar", "app.asar.org")

        logger.info("Patching app.asar")
        
        if os.path.isdir("tmp"):
            logger.info("Removing pre-existing tmp folder.")
            shutil.rmtree("tmp")
        logger.info("Extracting app.asar to tmp folder.")
        os.mkdir("tmp")
        os.system(f"npx asar extract app.asar tmp")

        patch_folder = os.path.join(resources_path, "tmp", "dist")

        with open(os.path.join(patch_folder, "store.html"), "r", encoding='utf-8') as f:
            content = f.read()
        
        with open(os.path.join(patch_folder, "store.html"), "w", encoding='utf-8') as f:
            f.write(content.replace("</html>","""
<script>
	function buttonPoll() {
	  const button = document.querySelector('button[aria-label=ダウンロード版でプレイ]');
	  const isUma = button && [...document.getElementsByTagName('h1')].filter(e => e.innerText.startsWith('ウマ娘 プリティーダービー')).length;
	  if (isUma)
		button.click();
	  else
		requestAnimationFrame(buttonPoll);
	}
	buttonPoll();
	</script>
</html>
            """))
        os.system(f"npx asar pack tmp app.asar")
        os.chdir(cwd_before)
        logger.info("DMM has been patched.")
    else:
        logger.warning("Could not find DMM folder to patch DMM.")


def unpatch_dmm():
    logger.info("Attempting to unpatch DMM.")
    resources_path = os.path.join(settings.get("dmm_path"), "resources")
    if os.path.isdir(resources_path):
        cwd_before = os.getcwd()
        os.chdir(resources_path)
        if os.path.isfile("app.asar.org"):
            logger.info("Reverting app.asar.")
            if os.path.isfile("app.asar"):
                attempts = 0
                while attempts < 5:
                    try:
                        os.remove("app.asar")
                        break
                    except PermissionError:
                        attempts += 1
                        logger.warning(f"Could not remove app.asar. Attempt {attempts}.")
                        time.sleep(1)
            shutil.copy("app.asar.org", "app.asar")
            os.remove("app.asar.org")
        if os.path.isdir("tmp"):
            logger.info("Removing tmp folder.")
            shutil.rmtree("tmp")
        os.chdir(cwd_before)
    else:
        logger.warning("Could not find DMM folder to unpatch DMM.")
