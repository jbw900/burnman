import os, sys, numpy as np
import matplotlib.pyplot as plt

lib_path = os.path.abspath('code/')
sys.path.append(lib_path)

from code import minerals 
from code import main as main
from code import seismic

### input variables ###
#######################

#INPUT for method
method = 'slb' # choose 'slb' (finite-strain, stixrude and lithgow-bertelloni, 2005) or 'mgd' (mie-gruneisen-debeye, matas et al. 2007)


phases = (minerals.user_mineral1(), minerals.Murakami_fp_LS()) #disregard second mineral. See code/minerals.py for reference to user_mineral1
amount_perovskite = 1.
molar_abundances = ( amount_perovskite, 1.0-amount_perovskite)


#seismic model for comparison:
seismic_model = seismic.prem() # pick from .prem() .slow() .fast() (see code/seismic.py)
number_of_points = 20 #set on how many depth slices the computations should be done
depths = np.linspace(700,2800, number_of_points)
#depths = seismic_model.internal_depth_list()
seis_p, seis_rho, seis_vp, seis_vs, seis_vphi = seismic_model.evaluate_all_at(depths)

        
geotherm = main.get_geotherm("brown_shankland")
temperature = [geotherm(p) for p in seis_p]

for ph in phases:
	ph.set_method(method)

print "Calculations are done for:"
for i in range(len(phases)):
	print molar_abundances[i], " of phase", phases[i].to_string()

mat_rho, mat_vs, mat_vp, mat_vphi, mat_K, mat_mu = main.calculate_velocities(seis_p, temperature, phases, molar_abundances)	

[rho_err,vphi_err,vs_err]=main.compare_with_seismic_model(mat_vs,mat_vphi,mat_rho,seis_vs,seis_vphi,seis_rho)
	

# PLOTTING

plt.subplot(2,2,1)
p1,=plt.plot(seis_p/1.e9,mat_vs,color='b',linestyle='-',marker='o',markerfacecolor='b',markersize=4,label='computation')
p2,=plt.plot(seis_p/1.e9,seis_vs,color='k',linestyle='-',marker='o',markerfacecolor='k',markersize=4,label='reference')
plt.title("Vs (km/s)")
plt.xlim(min(seis_p)/1.e9,max(seis_p)/1.e9)
plt.ylim(5.1,7.6)
plt.legend(loc='lower right')
plt.text(40,7.3,"misfit= %3.3f" % vs_err)

# plot Vphi
plt.subplot(2,2,2)
p1,=plt.plot(seis_p/1.e9,mat_vphi,color='b',linestyle='-',marker='o',markerfacecolor='b',markersize=4)
p2,=plt.plot(seis_p/1.e9,seis_vphi,color='k',linestyle='-',marker='o',markerfacecolor='k',markersize=4)
plt.title("Vphi (km/s)")
plt.xlim(min(seis_p)/1.e9,max(seis_p)/1.e9)
plt.ylim(7,12)
#	plt.legend([p1,p2],["Murakami (0.93 Pv, 0.07 fp)", "seismic model (PREM)"], loc=4)
plt.text(40,11.5,"misfit= %3.3f" % vphi_err)

# plot density
plt.subplot(2,2,3)
p1,=plt.plot(seis_p/1.e9,mat_rho,color='b',linestyle='-',marker='o',markerfacecolor='b',markersize=4)
p2,=plt.plot(seis_p/1.e9,seis_rho,color='k',linestyle='-',marker='o',markerfacecolor='k',markersize=4)
plt.title("density (kg/m^3)")
plt.xlim(min(seis_p)/1.e9,max(seis_p)/1.e9)
plt.text(40,5.3,"misfit= %3.3f" % rho_err)
plt.xlabel("Pressure (GPa)")


# plot geotherm
plt.subplot(2,2,4)
p1,=plt.plot(seis_p/1e9,temperature,color='r',linestyle='-',marker='o',markerfacecolor='r',markersize=4)
plt.title("Geotherm (K)")
plt.xlim(min(seis_p)/1.e9,max(seis_p)/1.e9)
plt.xlabel("Pressure (GPa)")

	


plt.savefig("example_user_input.png")
plt.show()