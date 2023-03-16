### This script renames all the files as the folder name + index + extension in its directory
from collections import Counter
import copy
import csv
import shutil
import os
import logging
from syslog import LOG_INFO


import pandas as pd
logging.basicConfig(format='[%(module)s | l.%(lineno)d] %(message)s')
logging.getLogger().setLevel(logging.INFO)
import argparse
import random

def import_dataset_to_classes(args):
    count = 0
    avoid_classes = ["D", "no_sign"]
    special_classes = ["M3b", "M4d1", "backward", "CE27"]
    for root, dirs, files in os.walk(args.dir):
        depth = root.replace(args.dir, '').count(os.sep)
        if depth == args.depth:
            logging.info('dirs=\n%s',dirs)
            for folder in dirs:
                if folder in avoid_classes:
                    continue
                if folder in special_classes:
                    logging.info("Folder %s in special_classes", folder)
                    continue
                if folder in os.listdir(args.new_dir):
                    for file in os.listdir(os.path.join(root, folder)):
                        shutil.copy(os.path.join(root, folder, file), os.path.join(args.new_dir, folder, file))
                        count += 1
                else:
                    # logging.info("Folder %s not in new_dir", folder)
                    if len(os.listdir(os.path.join(root, folder))) >= 3:
                        shutil.copytree(os.path.join(root, folder), os.path.join(args.new_dir, folder))
                        count += len(os.listdir(os.path.join(root, folder)))
                        logging.info('Created folder %s', folder)
    logging.info(f"Copied {count} images")

def get_superclasses_classes_dicts(args):
    """must provide : 
    - args.depth = depth at which class folders are in the tree, 
    - args.general_args in ('sc2c', 'c2sc')
    - args.superclasses-tree : superclasses dir"""
    c2sc = {}
    sc2c = {}
    for root, dirs, files in os.walk(args.superclasses_tree):
        # indent = len(root.replace(args.superclasses_tree, '').split(os.sep))
        # print('{}{}/'.format('| ' * (indent - 1), os.path.basename(root)))
        relative_root = root.replace(args.superclasses_tree, '')
        depth = relative_root.count(os.sep)
        if depth == args.depth:
            logging.info('dirs=\n%s',dirs)
            for folder in dirs:
                c2sc[folder] = tuple(relative_root.split(os.sep) + [folder])
                sc2c[tuple(relative_root.split(os.sep) + [folder])] = folder
    return sc2c, c2sc

def classes_to_superclasses(args):
    """must provide : 
    - args.depth = depth at which class foldres are in the tree, 
    - args.superclasses-tree : superclasses dir
    - args.dir : dir containing the classes folders
    - args.new_dir : new dir to create"""
    sc2c, c2sc = get_superclasses_classes_dicts(args)
    if not os.path.exists(args.new_dir):
        os.makedirs(args.new_dir)
    
    for label in os.listdir(args.dir):
        if label in c2sc:
            superclasses = c2sc[label]
            superclasses_path = os.path.join(args.new_dir, *superclasses)
            if not os.path.exists(superclasses_path):
                os.makedirs(superclasses_path)
            for file in os.listdir(os.path.join(args.dir, label)):
                shutil.copy(os.path.join(args.dir, label, file), os.path.join(superclasses_path, file))
        else:
            logging.info('class %s not found in c2sc',label)

def classes_tree_to_images(args):
    """must provide : 
    - args.depth = depth at which class folders are in the tree, 
    - args.superclasses-tree : superclasses dir
    - args.dir : dir containing the classes folders
    - args.new_dir : destination folder"""
    sc2c, c2sc = get_superclasses_classes_dicts(args)
    logging.info('c2sc=\n%s',c2sc)
    if not os.path.exists(args.new_dir):
        os.makedirs(args.new_dir)
    count = 0
    new_names = []
    for label in os.listdir(args.dir):
        if label in c2sc:
            superclass = c2sc[label]
            for file in os.listdir(os.path.join(args.dir, label)):
                if ")_" in file :
                    new_filename = "-".join(superclass) + f"_{file.split(')_')[1].split('.')[0]}.jpg"
                    new_names.append(new_filename)
                elif ")" in file or "png" in file or not "_" in file :
                    new_filename = "-".join(superclass) + f"_SD_{file.split('.')[0]}.jpg"
                    if new_filename in new_names:
                        logging.info('new_filename %s already exists',new_filename)
                        new_filename = "-".join(superclass) + f"_SD_{file.split('.')[0]}_{random.randint(0,100)}.jpg"
                    new_names.append(new_filename)
                else:
                    new_filename = "-".join(superclass) + f"_ETSD_{file.split('.')[0]}.jpg"
                    if new_filename in new_names:
                        logging.info('new_filename %s already exists',new_filename)
                        new_filename = "-".join(superclass) + f"_ETSD_{file.split('.')[0]}_{random.randint(0,100)}.jpg"
                    new_names.append(new_filename)
                shutil.copy(os.path.join(args.dir, label, file), os.path.join(args.new_dir, new_filename))
                count += 1
        else:
            logging.info('class %s not found in c2sc',label)
    logging.info('Copied %s files',count)

def superclasses_to_classes(args):
    """must provide : 
    - args.depth = depth at which class foldres are in the tree, 
    - args.superclasses-tree : superclasses dir
    - args.dir : dir containing the classes folders
    - args.new_dir : new dir to create"""
    sc2c, c2sc = get_superclasses_classes_dicts(args)
    if not os.path.exists(args.new_dir):
        os.makedirs(args.new_dir)
    
    # superclasses_paths = ["/".join(superclasses) for superclasses in sc2c]
    doubles = []
    count = 0
    for superclass in sc2c:
        if superclass[-1] in doubles:
            logging.info("class %s appears two times in leafs",superclass[-1])
        doubles.append(superclass[-1])
        
        if not os.path.exists(os.path.join(args.new_dir, superclass[-1])):
            os.makedirs(os.path.join(args.new_dir, superclass[-1]))
        for file in os.listdir(os.path.join(args.dir, *superclass)):
            shutil.copy(os.path.join(args.dir, *superclass, file), os.path.join(args.new_dir, superclass[-1], file))
            count += 1
    logging.info('Copied %s files',count)


def classes_tree_to_images(args):
    if not os.path.exists(args.new_dir):
        os.makedirs(args.new_dir)
    classes_tree_path = os.path.join(args.new_dir, "images_classes-tree")
    superclasses_tree_path = os.path.join(args.new_dir, "images_superclasses-tree")
    images_path = os.path.join(args.new_dir, "images")
    if not os.path.exists(classes_tree_path):
        os.makedirs(classes_tree_path)
    if not os.path.exists(superclasses_tree_path):
        os.makedirs(superclasses_tree_path)
    if not os.path.exists(images_path):
        os.makedirs(images_path)
    
    # if args.dir not classes_tree_path then copy it :
    if args.dir != classes_tree_path:
        for label in os.listdir(args.dir):
            if not os.path.exists(os.path.join(classes_tree_path, label)):
                os.makedirs(os.path.join(classes_tree_path, label))
            for file in os.listdir(os.path.join(args.dir, label)):
                shutil.copy(os.path.join(args.dir, label, file), os.path.join(classes_tree_path, label, file))
    args_c2sc = copy.deepcopy(args)
    args_c2sc.dir = classes_tree_path
    args_c2sc.new_dir = superclasses_tree_path
    classes_to_superclasses(args_c2sc)
    args_c2f = copy.deepcopy(args)
    args_c2f.dir = classes_tree_path
    args_c2f.new_dir = images_path
    classes_tree_to_images(args_c2f)

def images_to_classes_tree(args):
    """From a dir with images with names of the format 'category-superclass-class_id.jpg', 
    copy the images in new_dir structured by the classes"""
    assert args.dir is not None, "must provide a dir"
    assert args.new_dir is not None, "must provide a new_dir"
    if not os.path.exists(args.new_dir):
        os.makedirs(args.new_dir)

    images = os.listdir(args.dir)
    count = 0
    for image in images:
        category = image.split("-")[0]
        superclass = image.split("-")[1]
        _split = ("-".join(image.split("-")[2:])).split("_")
        class_id = "_".join(_split[:-1])

        if not os.path.exists(os.path.join(args.new_dir, class_id)):
            os.makedirs(os.path.join(args.new_dir, class_id))
        shutil.copy(os.path.join(args.dir, image), os.path.join(args.new_dir, class_id, image))
        count += 1
    logging.info('Copied %s files of %s',count,len(images))

def images_to_superclasses_tree(args):
    """From a dir with images with names of the format 'category-superclass-class_id.jpg', 
    copy the images in new_dir with the same structure as the superclasses"""
    assert args.dir is not None, "must provide a dir"
    assert args.new_dir is not None, "must provide a new_dir"
    if not os.path.exists(args.new_dir):
        os.makedirs(args.new_dir)

    images = os.listdir(args.dir)
    count = 0
    for image in images:
        category = image.split("-")[0]
        superclass = image.split("-")[1]
        _split = ("-".join(image.split("-")[2:])).split("_")
        class_id = "_".join(_split[:-1])
        new_path = os.path.join(args.new_dir, category, superclass, class_id)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        shutil.copy(os.path.join(args.dir, image), os.path.join(new_path,image))
        count += 1
    logging.info('Copied %s files of %s',count,len(images))

def count_tree_files(args):
    """must provide : 
    - args.dir"""
    counter = 0
    for root, dirs, files in os.walk(args.dir):
        counter += len(files)
    logging.info('counter=\n%s',counter)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('script', type=str, help='desired script to run. choices : \
        "get-superclasses-classes-dicts" \
        "classes-to-superclasses" \
        "superclasses-to-classes" \
        "classes_tree_to_images" \
        "classes_tree_to_images" \
        "import_dataset_to_classes" \
        "images_to_classes_tree" \
        "images_to_superclasses_tree" \
        "count-tree-files"') # from a dir with folders of files, creates a dir with all the same folders but the images converted to jpg
    arg_parser.add_argument('--dir', type=str, help='folder to rename', default=".")
    arg_parser.add_argument('--dir2', type=str, help='second folder, used by complete-dataset-with-dict', default=".")
    arg_parser.add_argument('--superclasses_tree', type=str, help='superclasses reference tree', default=".")
    
    arg_parser.add_argument('--new_dir', type=str, help='new folder, used by uncollapse', default="./uncollapsed")
    arg_parser.add_argument('--ratio', type=float, help='ratio of images to copy, used by random-pick', default=0.1)
    arg_parser.add_argument('--train_ratio', type=float, help='ratio of images to copy to train, used by make-validation-set', default=None)
    arg_parser.add_argument('--move', action='store_true', help='move files instead of copying them, used by random-pick')
    arg_parser.add_argument('--leave_unique', type=int, help='do not copy/move folders with <= leave_unique files, used by random-pick', default=None)
    arg_parser.add_argument('--csv_file', type=str, help='csv file containing the class of each image, used by uncollapse_from_csv', default=None)
    arg_parser.add_argument('--general_arg', type=str, help='general argument', default=None)
    arg_parser.add_argument('--starting_with', type=str, help='starting with', default=None)
    arg_parser.add_argument('--deeper', action='store_true', help='deeper', default=False)
    arg_parser.add_argument('--depth', type=int, help='depth', default=0)
    args = arg_parser.parse_args()

    
    if args.script == "get-superclasses-classes-dicts":
        sc2c, c2sc = get_superclasses_classes_dicts(args)
        print(sc2c)
        print(c2sc)
    
    elif args.script == "classes-to-superclasses":
        classes_to_superclasses(args)
    
    elif args.script == "superclasses-to-classes":
        superclasses_to_classes(args)
    
    elif args.script == "count-tree-files":
        count_tree_files(args)
    
    elif args.script == "classes_tree_to_images":
        classes_tree_to_images(args)
    
    elif args.script == "classes_tree_to_images":
        classes_tree_to_images(args)
    
    elif args.script == "import_dataset_to_classes":
        import_dataset_to_classes(args)
    
    elif args.script == "images_to_classes_tree":
        images_to_classes_tree(args)

    elif args.script == "images_to_superclasses_tree":
        images_to_superclasses_tree(args)