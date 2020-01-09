Examples of execution commands used for running ICPR's experiments:

nice -n 20 ./pattern_theory.py hof-hog-spect400_TestUnits global_hofhogspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out3 &
nice -n 20 ./pattern_theory.py cnn-cnnflow-spect400_TestUnits global_cnncnnflowspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out2 &
nice -n 20 ./pattern_theory.py cnn-spect400_TestUnits global_cnnspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out_cnnspect400 &
nice -n 20 ./pattern_theory.py hog-spect400_TestUnits global_hogspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out_hogspect400 &

Examples of execution using ConceptNet priors:

nice -n 20 ./pattern_theory.py hof-hog-spect400_TestUnits conceptnet_hofhogspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out3 &
nice -n 20 ./pattern_theory.py cnn-cnnflow-spect400_TestUnits conceptnet_cnncnnflowspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out2 &
nice -n 20 ./pattern_theory.py cnn-spect400_TestUnits conceptnet_cnnspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out_cnnspect400 &
nice -n 20 ./pattern_theory.py hog-spect400_TestUnits conceptnet_hogspect400 PilotExpICPR16 regular bond_weights_ow1.0_sw1.0.txt 0.0 > out_hogspect400 &
