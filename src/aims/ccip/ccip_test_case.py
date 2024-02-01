import csv
import unittest

from reefscanner.basic_model.basic_model import BasicModel
from reefscanner.basic_model.progress_no_queue import ProgressNoQueue
from reefscanner.basic_model.survey import Survey

from aims import utils
from aims.ccip.cull_splitter import CullSplitter
from aims.ccip.culls import Culls
from aims.ccip.polygons import Polygons
from aims.ccip.tow_splitter import TowSplitter
from aims.ccip.tows import Tows
from aims.model.cots_detection_list import CotsDetectionList


class CcipTestCase(unittest.TestCase):
    def test_read_tows_file(self):
        tows = Tows("data/tows")
        print(str(tows.tows[0].time))
        self.assertEqual(str(tows.tows[0].time), "2024-01-16 23:27:00")
        print(len(tows.tows))
        self.assertEqual(len(tows.tows), 36)

    def test_read_polygons_file(self):
        polygons = Polygons("../test/data/CCIP_PolygonDetails.csv")
        print(str(polygons.polygons[0].start_time))
        self.assertEqual(str(polygons.polygons[0].start_time), "2024-01-16 23:26:56")
        print(len(polygons.polygons))
        self.assertEqual(len(polygons.polygons), 49)

        culls = Culls("data/culls")
        print(culls.culls[0].name)
        self.assertEqual(culls.culls[0].name, "U/N_21-057_44")
        print(len(culls.culls))
        self.assertEqual(len(culls.culls), 3)

        polygons.add_cull_data(culls)

    def test_build_detections(self):
        tow_splitter = TowSplitter("C:/greg/bpm/manta_tow_data",
                                   "D:/reefscan/2024-01-17/20240116_232631_Seq01-21-057-ReefScan Deep 21-057 Channel",
                                   "d:/reefscan_ccip_split/2024-01-17/20240116_232631_Seq01-21-057-ReefScan Deep 21-057 Channel")
        tow_splitter.build_detections()
        print(tow_splitter.detections_by_first_photo)

    def test_split_tows(self):
        tow_splitter = TowSplitter("data/t1/ccip-manta.json",
                                   "D:/reefscan/2024-01-17/20240116_232631_Seq01-21-057-ReefScan Deep 21-057 Channel",
                                   "d:/reefscan_ccip_split/2024-01-17/20240116_232631_Seq01-21-057-ReefScan Deep 21-057 Channel")
        tow_splitter.split()
        dicts = tow_splitter.tows.dicts()
        dicts.append(tow_splitter.between_tow.dict())
        print(dicts)

        file_name = "d:/reefscan_ccip_split/results.csv"
        with open(file_name, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=dicts[0].keys(), lineterminator="\n")
            writer.writeheader()
            for dict in dicts:
                writer.writerow(dict)

    def test_split_all_tows(self):
        progress_queue = ProgressNoQueue()
        # basic_model.set_data_folders("D:/Trip7785_DaviesReef_CoralAUV_ReefScanTesting/ReefScan", "")
        # basic_model.set_data_folders("E:/heron_island_tech_2022", r"\\192.168.3.2\images")
        primary_data_folder = "E:/reefscan"
        backup_data_folder = None
        basic_model = BasicModel()

        basic_model.set_data_folders(primary_data_folder, backup_data_folder, r"\\192.168.3.2\images")

        basic_model.slow_network = False
        basic_model.read_from_files(progress_queue, camera_connected=False)
        all_dicts = []
        tow_splitter = TowSplitter("C:/greg/bpm/manta_tow_data")
        for s in basic_model.surveys_data.values():
            survey: Survey = s
            input_folder = survey.folder
            print(input_folder)
            output_folder = utils.replace_last(input_folder, "reefscan", "reefscan_ccip_split")
            tow_splitter.input_folder = input_folder
            tow_splitter.output_folder = output_folder
            tow_splitter.split()
            all_dicts.append(tow_splitter.between_tow.dict())

        dicts = tow_splitter.tows.dicts()
        all_dicts.extend(dicts)
        file_name = "e:/reefscan_ccip_split/results.csv"
        with open(file_name, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_dicts[0].keys(), lineterminator="\n")
            writer.writeheader()
            for dict in all_dicts:
                writer.writerow(dict)

    def test_split_all_polys(self):
        progress_queue = ProgressNoQueue()
        # basic_model.set_data_folders("D:/Trip7785_DaviesReef_CoralAUV_ReefScanTesting/ReefScan", "")
        # basic_model.set_data_folders("E:/heron_island_tech_2022", r"\\192.168.3.2\images")
        primary_data_folder = "E:/reefscan"
        backup_data_folder = None
        basic_model = BasicModel()

        basic_model.set_data_folders(primary_data_folder, backup_data_folder, r"\\192.168.3.2\images")

        basic_model.slow_network = False
        basic_model.read_from_files(progress_queue, camera_connected=False)
        all_dicts = []
        cull_splitter = CullSplitter("C:/greg/bpm/cull_data", "../test/data/CCIP_PolygonDetails.csv")
        for s in basic_model.surveys_data.values():
            survey: Survey = s
            input_folder = survey.folder
            print(input_folder)
            output_folder = utils.replace_last(input_folder, "reefscan", "reefscan_ccip_split_culls")
            cull_splitter.input_folder = input_folder
            cull_splitter.output_folder = output_folder
            cull_splitter.split()
            all_dicts.append(cull_splitter.between_poly.dict())

        dicts = cull_splitter.polygons.dicts()
        all_dicts.extend(dicts)
        file_name = "e:/reefscan_ccip_split_culls/results.csv"
        with open(file_name, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_dicts[0].keys(), lineterminator="\n")
            writer.writeheader()
            for dict in all_dicts:
                writer.writerow(dict)




    def test_cache_all(self):
        progress_queue = ProgressNoQueue()
        # basic_model.set_data_folders("D:/Trip7785_DaviesReef_CoralAUV_ReefScanTesting/ReefScan", "")
        # basic_model.set_data_folders("E:/heron_island_tech_2022", r"\\192.168.3.2\images")
        primary_data_folder = "E:/reefscan"
        backup_data_folder = None
        basic_model = BasicModel()

        basic_model.set_data_folders(primary_data_folder, backup_data_folder, r"\\192.168.3.2\images")

        basic_model.slow_network = False
        basic_model.read_from_files(progress_queue, camera_connected=False)
        all_dicts = []
        for s in basic_model.surveys_data.values():
            survey: Survey = s
            input_folder = survey.folder
            cots_detection_list = CotsDetectionList()
            cots_detection_list.read_eod_files(input_folder, samba=False, use_cache=True)

