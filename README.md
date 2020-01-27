# eventunderstanding
As per our conversation over WhatsApp, attached is the PT code that I used for the QAM/WACV papers. Note that it is based on Python2.7. I have not gotten around to updating it to Python3. I have included the input files (top-k labels) as used for the Breakfast Actions dataset and its subsequent evaluation code (as obtained from Fillipe).

Note that the code as it is right now still connects to the ConceptNet web API (official link: http://api.conceptnet.io/) to compute priors. I was able to recreate the results when we had our own ConceptNet server. I have been working on transferring the process to a local CSV copy since access to the API is limited, but have not been able to exactly recreate the performance (we lose ~0.5 - 1% accuracy). The programs do not have any arguments as of now. All paths are encoded as variables within the code.

I have tried to add some comments so it should be fairly straightforward to understand (I hope!). 

1. What is in the zip file?
2. Main file: HRC_PatternTheory.py 
3. Constructing contextualization priors: hierarchicalPriors.py (WACV/QAM paper)
4. Constructing similarity priors: conceptnet_prior.py (CRV paper)
5. Visualizing contextualized interpretation: visualize_contextualization.py --> Note: input is the final grounded generators (from HRC_PatternTheory.py) and the output is the contextualized interpretation. I split it into separate parts to speed up computation.
6. S1_PreProcessFiles/: The folder contains the input labels (top-k) required to run PT for Split 1 of the Breakfast Actions dataset. You can recreate the format for any dataset/video you want.
7. HRC_Priors/: The folder contains example priors needed for computing semantic energy. I have included all priors required to recreate numbers for both QAM/WACV (OnlyHC_IsA) and CRV (Similarity_Priors) papers. You can also recreate Fillipe's numbers using the domainPriors folder as the source of priors.
8. calcPerformance.py: Computing the accuracy for breakfast actions. The ground truth is part of the output filename and is used to evaluate. I followed this format to use Fillipe's convention for evaluation.
BA_S1_Out/: Example output folder.

I hope the code is easy to follow and that the instructions are detailed enough, but do let me know if you have any questions.
