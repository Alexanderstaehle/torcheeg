import unittest
import os
import random
import shutil

from torcheeg.model_selection import train_test_split_trial_per_subject
from torcheeg.datasets import DEAPDataset


class TestTrainTestSplitTrialPerSubject(unittest.TestCase):
    def setUp(self):
        shutil.rmtree('./tmp_out/')
        os.mkdir('./tmp_out/')

    def test_train_test_split_trial_per_subject(self):
        io_path = f'./tmp_out/deap_{"".join(random.sample("zyxwvutsrqponmlkjihgfedcba", 20))}'
        root_path = './tmp_in/data_preprocessed_python'

        dataset = DEAPDataset(io_path=io_path, root_path=root_path)

        split_path = f'./tmp_out/split_{"".join(random.sample("zyxwvutsrqponmlkjihgfedcba", 20))}'

        train_dataset, test_dataset = train_test_split_trial_per_subject(dataset=dataset, split_path=split_path, subject=0)
        
        self.assertEqual(len(train_dataset), 1920)
        self.assertEqual(len(test_dataset), 480)


if __name__ == '__main__':
    unittest.main()