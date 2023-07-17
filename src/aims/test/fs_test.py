import logging

# print (os.path.exists("//pearl/temp/gcoleman"))
# print (str(os.listdir("//pearl/temp/gcoleman")))
from aims.state import state
from aims2.operations2.archive_checker import ArchiveChecker
logging.basicConfig(level=logging.INFO)
logger_smb = logging.getLogger('smbprotocol')
logger_smb.setLevel(level=logging.WARNING)

state.set_data_folders()
archive_checker = ArchiveChecker()
archive_checker.run()
