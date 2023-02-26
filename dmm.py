import shutil
import os
import hashlib
from loguru import logger
import util

def patch_dmm(dmm_path):
    logger.info("Patching DMM.")
    resources_path = os.path.join(dmm_path, "resources")
    if not os.path.isdir(resources_path):
        logger.error("Could not find DMM folder to patch DMM.")
        util.show_alert_box("Error", "Could not find DMM folder to patch DMM.\nPlease check if the path to DMMGamePlayer's install folder is correct in umasettings.json.")
        return
    if os.path.isfile(os.path.join(resources_path, "app.hash")):
        logger.debug("Found remnants of a patch. Checking hash.")
        with open(os.path.join(resources_path, "app.hash"), "r", encoding='utf-8') as f:
            hash_before = f.read()

        with open(os.path.join(resources_path, "app.asar"), "rb") as f:
            app_hash = hashlib.md5(f.read()).hexdigest()

        if hash_before == app_hash:
            logger.debug("Hashes match. No need to patch.")
            return
        logger.debug("Hashes do not match.")

    logger.debug("Starting DMM patch.")
    cwd_before = os.getcwd()
    os.chdir(resources_path)

    logger.debug("Backing up app.asar.")
    shutil.copy("app.asar", "app.asar.org")

    if os.path.exists("tmp"):
        logger.debug("Removing pre-existing tmp folder.")
        shutil.rmtree("tmp")
    logger.debug("Extracting app.asar to tmp folder.")
    os.mkdir("tmp")
    os.system("npx asar extract app.asar tmp")

    logger.debug("Patching store.html.")
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

    logger.debug("Packing app.asar.")
    os.system("npx asar pack tmp app.asar")
    logger.debug("DMM has been patched.")

    logger.debug("Removing tmp folder.")
    shutil.rmtree("tmp")

    logger.debug("Creating hash file.")
    with open(os.path.join(resources_path, "app.asar"), "rb") as f:
        app_hash = hashlib.md5(f.read()).hexdigest()
    with open(os.path.join(resources_path, "app.hash"), "w", encoding='utf-8') as f:
        f.write(app_hash)

    os.chdir(cwd_before)
    logger.info("Patching complete.")


def unpatch_dmm(dmm_path):
    logger.info("Attempting to unpatch DMM.")
    resources_path = os.path.join(dmm_path, "resources")
    if os.path.isdir(resources_path):
        cwd_before = os.getcwd()
        os.chdir(resources_path)
        if os.path.isfile("app.asar.org"):
            logger.debug("Reverting app.asar.")
            if os.path.isfile("app.asar"):
                os.remove("app.asar")
            shutil.copy("app.asar.org", "app.asar")
            os.remove("app.asar.org")
        if os.path.isdir("tmp"):
            logger.debug("Removing tmp folder.")
            shutil.rmtree("tmp")
        if os.path.isfile("app.hash"):
            logger.debug("Removing hash file.")
            os.remove("app.hash")
        os.chdir(cwd_before)
    else:
        logger.warning("Could not find DMM folder to unpatch DMM.")


def start():
    logger.info("Sending DMM to the Umamusume page.")
    os.system("Start dmmgameplayer://play/GCL/umamusume/cl/win")
