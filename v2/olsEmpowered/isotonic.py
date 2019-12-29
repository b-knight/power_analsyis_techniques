import numpy as np
import pandas as pd
from olsEmpowered import interpolation
from sklearn.isotonic import IsotonicRegression

class isotonic(interpolation.interpolation):

    # constructor
    def __init__(self, sim_data_ob,
                 rejection_region = 0.05,
                 desired_power = 0.8,
                 precision = 0.025,
                 search_orders = 1,
                 sims_per_point = 200):
        
        # set class variables
        self.rejection_region     = rejection_region
        self.desired_power        = desired_power
        self.precision            = precision
        self.search_orders        = search_orders
        self.dv_name              = sim_data_ob.dv_name     
        self.dv_cardinality       = sim_data_ob.dv_cardinality  
        self.treatment_variable   = sim_data_ob.treatment_variable  
        self.absolute_effect_size = sim_data_ob.absolute_effect_size    
        self.sample_size          = sim_data_ob.sample_size  
        self.covariates           = sim_data_ob.covariates       
        self.data                 = sim_data_ob.data
        self.sims_per_point       = sims_per_point
        
            
    def isotonic_interpolation(self):

        results_dict = {}
        parent_candidates   = []               
        parent_results      = []
              
        parent_candidates.append(self.set_lower_bound())
        parent_candidates.append(self.set_starting_value())
        parent_candidates.append(self.set_upper_bound())
                
        parent_sims_used    = 0
        parent_seconds_used = 0
        
        for i in parent_candidates:
            power_est, sims_used, secs_taken = self.assess_power(i, self.sims_per_point)
            parent_results.append(power_est)
            parent_sims_used    += sims_used
            parent_seconds_used += secs_taken
            
        if parent_results[0] <= 0.05:
            j = int(parent_candidates[0] + ((parent_candidates[1] - parent_candidates[0])/2))
            parent_candidates.append(j)
            power_est, sims_used, secs_taken = self.assess_power(j, self.sims_per_point)
            parent_results.append(power_est)
            parent_sims_used    += sims_used
            parent_seconds_used += secs_taken  
            parent_candidates.sort() 
            parent_results.sort() 
            
        if parent_results[-1] >= 0.95:
            k = int(parent_candidates[-2] + ((parent_candidates[-1] - parent_candidates[-2])/2))
            parent_candidates.append(k)
            power_est, sims_used, secs_taken = self.assess_power(k, self.sims_per_point)
            parent_results.append(power_est)
            parent_sims_used    += sims_used
            parent_seconds_used += secs_taken
            parent_candidates.sort() 
            parent_results.sort() 

        current_n = 0
        current_p = 0

        def isotonic_child(iso_candidates, iso_results):

            nonlocal current_n 
            nonlocal current_p
            nonlocal parent_candidates
            nonlocal parent_results 
            nonlocal parent_sims_used
            nonlocal parent_seconds_used

            iso_reg = IsotonicRegression().fit(iso_results, iso_candidates)
            current_n = int(iso_reg.predict([self.desired_power])) 
            parent_candidates.append(current_n)
            current_p, sims_used, secs_taken = self.assess_power(current_n, 
                                                                 self.sims_per_point)
            parent_results.append(current_p)
            parent_sims_used    += sims_used
            parent_seconds_used += secs_taken

            return iso_candidates, iso_results   

        iso_candidates = parent_candidates
        iso_results    = parent_results  

        while abs(current_p - self.desired_power) > self.precision:
            iso_candidates, iso_results = isotonic_child(iso_candidates, 
                                                         iso_results)

        results_dict.update({'candidates': iso_candidates})
        results_dict.update({'power': iso_results})
        results_dict.update({'sims_used': parent_sims_used})
        results_dict.update({'seconds_used': parent_seconds_used})
        results_dict.update({'status': 0})

        return current_n, current_p,  pd.DataFrame(results_dict) 