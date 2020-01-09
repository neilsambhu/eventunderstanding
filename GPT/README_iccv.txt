Organizing test features by units:
    -- use the "prepare_unit_test_features" function from script 'prepare_test_features.py'
    -- write something like the following in the main function:
        for i in range(1, n_folds+1):
            prepare_unit_test_features(split_number=i,output_path='unit_test_features')

Constructing test histograms:
    -- use the "construct_test_histograms" function from script 'build_test_histograms.py'
    -- write something like the following in the main function:
        pool = Pool(n_folds)
        for i in range(1, n_folds+1):
            tasks.append(('unit_test_features/s'+str(i),'unit_test_features/s'+str(i)+'/histogram/test',
                      'train_features/s'+str(i)+'/codebook', './GMMBoVW', False, 0, window_size)) #, 4, os.getpid()))
        pool.map(construct_test_histograms, tasks)

Converting the assembled test histograms to libsvm format:
    -- use the function "convert_to_libsvm_format" from script 'build_test_histograms.py'
    -- write something like the following in the main function:
        input_path_list = []
        feature_file_list = []
        for i in range(1, n_folds+1):
            input_path_list.append('test_features/s'+str(i)+'/histogram/test')
        recursive_file_search(input_path_list, feature_file_list, ['hog','hof'])
        for file in feature_file_list:
            print 'CONVERTING '+file
            convert_to_libsvm_format(file,1)

Generating pattern theory framework input files that point to the test features:
    -- run the script 'organize_test_histograms.py' as it is (make sure you change the input path when needed)
    -- ./organize_test_histograms.py <split_number> <# of segments> <segment granularity>
       Ex.: ./organize_test_histograms.py 1 1 0
            (for experiments for fold 1 with 1 video segment of unit size)


Examples of how to run performance script:

./measure_performance.py /home/students/fillipe/Breakfast_Final/lab_raw /home/students/fillipe/ICCV2015/ow0.5_sw0.5_ft0.1/s2_1seg_results
