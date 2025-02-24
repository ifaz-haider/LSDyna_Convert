inp_file="//home//ihaider//Projects//Bruce-FSI//github//LSDyna_Convert//input_files//mesh_euler.inp"
k_file="//home//ihaider//Projects//Bruce-FSI//github//LSDyna_Convert//input_files//mesh_euler_converted.k"

#node numbers associated with each face
abq_surf_def={"S1": [1,2,3,4], "S2":[5,8,7,6], "S3": [1,5,6,2], "S4": [2,6,7,3], "S5": [3,7,8,4], "S6": [4,8,5,1] }


#dictionary indexes based on names given in the sample .k file
nodeset_ssid = {"K1A": 999, "K2A": 888, "K1B": 777, "K2B": 666}
segmentset_ssid = {"FACEK1A":555, "FACEK2A": 444, "FACEK1B": 333, "FACEK2B": 222, "OUTERS": 111, "ELSURF": 1111}
elementset_ssid = {"FLUID1": 2222, "FLUID2": 3333}
