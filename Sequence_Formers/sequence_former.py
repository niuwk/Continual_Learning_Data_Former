import os.path
import torch
from copy import deepcopy
from continuum_loader import ContinuumSetLoader

if os.path.exists("Sequence_Formers"):  # check if we are in the folder Continual_Learning_Data_Former
    from data_utils import load_data, check_and_Download_data, get_images_format
else:
    from ..data_utils import load_data, check_and_Download_data, get_images_format


class Sequence_Former(ContinuumSetLoader):
    '''Parent Class for Sequence Formers'''

    def __init__(self, path, dataset, tasks_number, scenario, num_classes, download=False, train=True, path_only=False, verbose=False):

        self.tasks_number = tasks_number
        self.num_classes = num_classes
        self.dataset = dataset
        self.i = os.path.join(path, "Datasets")
        self.o = os.path.join(path, "Continua", self.dataset)
        self.train = train
        self.imageSize, self.img_channels = get_images_format(self.dataset)
        self.scenario = scenario
        self.verbose = verbose
        self.path_only = path_only
        self.download = True

        # if self.path_only we don't load data but just path
        # data will be loaded online while learning
        # it is considered as light mode this continual dataset are easy to generate and load
        if self.path_only:
            light_id = '_light'
        else:
            light_id = ''

        if not os.path.exists(self.o):
            os.makedirs(self.o)

        if self.train:
            self.out_file = os.path.join(self.o, '{}_{}_train{}.pt'.format(self.scenario, self.tasks_number, light_id))
        else:
            self.out_file = os.path.join(self.o, '{}_{}_test{}.pt'.format(self.scenario, self.tasks_number, light_id))

        check_and_Download_data(self.i, self.dataset, scenario=self.scenario, download=self.download)

        if self.download or not os.path.isfile(self.out_file):
            self.formating_data()
        else:
            self.continuum = torch.load(self.out_file)

        super(Sequence_Former, self).__init__(self.continuum)

    def select_index(self, ind_task, y):
        """
        This function help to select data in particular if needed
        :param ind_task: task index in the sequence
        :param y: data label
        :return: class min, class max, and index of data to keep
        """
        return 0, self.num_classes - 1, torch.arange(len(y))

    def transformation(self, ind_task, data):
        """
        Apply transformation to data if needed
        :param ind_task: task index in the sequence
        :param data: data to process
        :return: data post processing
        """
        if not ind_task < self.tasks_number:
            raise AssertionError("Error in task indice")
        return deepcopy(data)

    def label_transformation(self, ind_task, label):
        """
        Apply transformation to label if needed
        :param ind_task: task index in the sequence
        :param label: label to process
        :return: data post processing
        """
        if not ind_task < self.tasks_number:
            raise AssertionError("Error in task indice")
        return label

    @staticmethod
    def get_valid_ind(i_tr):
        # it is time to taxe train for validation
        len_valid = int(len(i_tr) * 0.2)
        indices = torch.randperm(len(i_tr))

        valid_ind = indices[:len_valid]
        train_ind = indices[len_valid:]

        i_va = i_tr[valid_ind]
        i_tr = i_tr[train_ind]

        return i_tr, i_va

    def create_task(self, ind_task, x_, y_):

        # select only the good classes
        class_min, class_max, i_tr = self.select_index(ind_task, y_)

        #_, _, i_te = self.select_index(ind_task, y_te)
        #i_tr, i_va = self.get_valid_ind(i_tr)

        x_t = self.transformation(ind_task, x_)
        #x_tr_t = self.transformation(ind_task, x_tr[i_tr])
        #x_va_t = self.transformation(ind_task, x_tr[i_va])
        #x_te_t = self.transformation(ind_task, x_te[i_te])

        y_t = self.label_transformation(ind_task, y_)
        #y_tr_t = self.label_transformation(ind_task, y_tr[i_tr])
        #y_va_t = self.label_transformation(ind_task, y_tr[i_va])
        #y_te_t = self.label_transformation(ind_task, y_te[i_te])

        if self.verbose and self.path_only:
            print("Task : {}".format(ind_task))
            ind = torch.randperm(len(x_t))[:10]
            #ind = torch.randperm(len(x_tr_t))[:10]
            #print(x_tr_t[ind])
            #ind = torch.randperm(len(x_va_t))[:10]
            #print(x_va_t[ind])
            #ind = torch.randperm(len(x_te_t))[:10]
            #print(x_te_t[ind])

        return class_min, class_max, x_t, y_t

    def prepare_formatting(self):
        pass

    def formating_data(self):

        self.prepare_formatting()

        # variable to save the sequence
        self.continuum = []

        x_, y_ = load_data(self.dataset, self.i, self.train)

        for ind_task in range(self.tasks_number):

            c1, c2, x_t, y_t = self.create_task(ind_task, x_, y_)
            self.continuum.append([(c1, c2), x_t, y_t])

        if not self.path_only:
            print(self.continuum[0][1].shape)
            print(self.continuum[0][1].mean())
            print(self.continuum[0][1].std())

        torch.save(self.continuum, self.out_file)