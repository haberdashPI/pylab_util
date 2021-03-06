import scipy
import numpy as np
import patsy
import blmm
from nu_wright_lab_util.sample_stats import *

model1 = blmm.load_model('lmm1',use_package_cache=True)
model2 = blmm.load_model('lmm2',use_package_cache=True)
model2_nf = blmm.load_model('lmm2_nf',use_package_cache=True)
rmodel2 = blmm.load_model('rlmm2',use_package_cache=True)
model3 = blmm.load_model('lmm3',use_package_cache=True)
model4 = blmm.load_model('lmm4',use_package_cache=True)
model5 = blmm.load_model('lmm5',use_package_cache=True)

def setup_groups(df,grouping):
  df = df.reset_index()
  grouped = df.groupby(grouping)
  gdfindices = np.zeros(len(grouped.groups),'int_')
  gg = np.zeros(df.shape[0],'int_')

  for i,key in enumerate(np.sort(grouped.groups.keys())):
    gg[grouped.groups[key]] = i
    gdfindices[i] = grouped.groups[key][0]

  gdf = df.iloc[gdfindices,:].copy()

  return gdf,gg

def setup_newgroups(df,model,ix):
  grouping = model.groups[ix]['grouping']
  gdf,_ = setup_groups(model.df,grouping)
  groups = gdf[grouping].copy()
  groups['ix'] = np.arange(groups.shape[0])
  group_indices = dict(zip(list(groups[grouping[0]]),list(groups['ix'])))

  oldgroups = model.df[grouping[0]].unique()
  allgroups = pd.Series(df[grouping[0]].unique())

  # for now, I don't allow new groups, only the ones analyzed
  # in the orginal data. I can implement this later.
  if not allgroups.isin(oldgroups).all():
    print ("WARNING: new group inference is not implemented, ignoring this,"+
           " assuming you will marginalize out the new group.")

  gg = df[grouping[0]].apply(lambda g: group_indices.get(g,0))

  return gdf,gg

def dfmatrices(df,model):
  A = patsy.dmatrix(model.A.design_info,df,return_type='dataframe')
  # avoids silently failing on legancy code that uses multiple groups
  # (which I no longer support)
  assert all(map(lambda x: len(x['grouping']) == 1,model.groups))

  gdf_1,gg_1 = setup_newgroups(df,model,0)

  B_1 = patsy.dmatrix(model.B[0].design_info,df,return_type='dataframe')
  G_1 = patsy.dmatrix(model.G.design_info,gdf_1,return_type='dataframe')

  if len(model.groups) == 1:
    return A,[B_1],G_1,[gg_1]

  if len(model.groups) >= 2:
    gdf_2,gg_2 = setup_newgroups(df,model,1)
    B_2 = patsy.dmatrix(model.B[1].design_info,df,return_type='dataframe')

    if len(model.groups) == 2:
      return A,[B_1,B_2],G_1,[gg_1,gg_2]

  if len(model.groups) >= 3:
    gdf_3,gg_3 = setup_newgroups(df,model,2)
    B_3 = patsy.dmatrix(model.B[2].design_info,df,return_type='dataframe')

    if len(model.groups) == 2:
      return A,[B_1,B_2,B_3],G_1,[gg_1,gg_2,gg_3]

  if len(model.groups) >= 4:
    gdf_4,gg_4 = setup_newgroups(df,model,3)
    B_4 = patsy.dmatrix(model.B[3].design_info,df,return_type='dataframe')

    if len(model.groups) == 4:
      return A,[B_1,B_2,B_3,B_4],G_1,[gg_1,gg_2,gg_3,gg_4]

  if len(model.groups) == 5:
    gdf_5,gg_5 = setup_newgroups(df,model,4)
    B_5 = patsy.dmatrix(model.B[4].design_info,df,return_type='dataframe')

    return A,[B_1,B_2,B_3,B_4,B_5],G_1,[gg_1,gg_2,gg_3,gg_4,gg_5]

  return None

def lmm(mean_formula,df,groups,eps_prior=1,fixed_prior=1,robust=False):
  #assert (len(groups) == 1) and (len(groups) <= 3)
  assert (len(groups) in range(1,6))

  y,A = patsy.dmatrices(mean_formula,df,return_type='dataframe')

  gdf_1,gg_1 = setup_groups(df,groups[0]['grouping'])
  B_1 = patsy.dmatrix(groups[0]['formula'],df,return_type='dataframe')
  G_1 = patsy.dmatrix(groups[0]['group_formula'],gdf_1,return_type='dataframe')

  if len(groups) == 1:
      model = LmmModel(df,mean_formula,groups,robust,
                       y,A,[gdf_1],[gg_1],[B_1],G_1,
                       eps_prior,fixed_prior)

  if len(groups) >= 2:
    gdf_2,gg_2 = setup_groups(df,groups[1]['grouping'])

    B_2 = patsy.dmatrix(groups[1]['formula'],df,return_type='dataframe')

    if len(groups) == 2:
      model = LmmModel(df,mean_formula,groups,robust,
                       y,A,[gdf_1,gdf_2],[gg_1,gg_2],
                       [B_1,B_2],G_1,
                       eps_prior,fixed_prior)

  if len(groups) >= 3:
    gdf_3,gg_3 = setup_groups(df,groups[2]['grouping'])

    B_3 = patsy.dmatrix(groups[2]['formula'],df,return_type='dataframe')
    if len(groups) == 3:
      model = LmmModel(df,mean_formula,groups,robust,
                       y,A,[gdf_1,gdf_2,gdf_3],[gg_1,gg_2,gg_3],

                       [B_1,B_2,B_3],G_1,eps_prior,fixed_prior)

  if len(groups) >= 4:
    gdf_4,gg_4 = setup_groups(df,groups[3]['grouping'])

    B_4 = patsy.dmatrix(groups[3]['formula'],df,return_type='dataframe')

    if len(groups) == 4:
      model = LmmModel(df,mean_formula,groups,robust,
                      y,A,[gdf_1,gdf_2,gdf_3,gdf_4],[gg_1,gg_2,gg_3,gg_4],

                      [B_1,B_2,B_3,B_4],G_1,eps_prior,fixed_prior)

  if len(groups) == 5:
    gdf_5,gg_5 = setup_groups(df,groups[4]['grouping'])

    B_5 = patsy.dmatrix(groups[4]['formula'],df,return_type='dataframe')

    if len(groups) == 5:
      model = LmmModel(df,mean_formula,groups,robust,
                      y,A,[gdf_1,gdf_2,gdf_3,gdf_4,gdf_5],
                      [gg_1,gg_2,gg_3,gg_4,gg_5],

                      [B_1,B_2,B_3,B_4,B_5],G_1,eps_prior,fixed_prior)

  return model


class LmmModel(object):
  def __init__(self,df,mean_formula,groups,robust,y,A,gdf,gg,
               B,G,eps_prior,fixed_prior):
    self.fit = None
    self.mean_formula = mean_formula
    self.groups = groups
    self.df = df
    self.y = np.squeeze(y)
    self.A = A
    self.gdf = gdf
    self.gg = gg
    self.B = B
    self.G = G
    self.eps_prior = eps_prior
    self.fixed_prior = fixed_prior
    self.robust = robust

  def predict(self,df=None,marginalize=[],randomize=[],meanonly=False,
              use_dataframe=False):
    if df is not None:
      df = df.copy()
      A,B,G,gg = dfmatrices(df,self)
    else:
      df = self.df
      A = self.A
      B = self.B
      G = self.G
      gg = self.gg

    if self.A.shape[1] > 1:
      y_hat = np.einsum('ij,kj->ik', A,self.fit['alpha'])
    elif self.A.shape[1] == 1:
      y_hat = np.einsum('ij,kj->ik', A,self.fit['alpha'][:, np.newaxis])
    else:
      y_hat = 0

    if 0 in marginalize:
      y_hat += (np.einsum('ik,jlk->ij', B[0],self.fit['beta_1']) /
                self.fit['beta_1'].shape[1])
    elif (0 in randomize) or meanonly:
      # samples, groups, predictors
      mean_1 = np.einsum('ik,jkh->jih',G,self.fit['gamma_1'])
      # samples, groups, predictors
      if not meanonly:
        z_1 = np.random.normal(size=(mean_1.shape[1],mean_1.shape[2]))
        cov_1 = np.einsum('ij,ijk,hj->ihj',self.fit['tau_1'],
                          self.fit['L_Omega_1'],z_1)
        mu = mean_1 + cov_1
      else:
        mu = mean_1
      y_hat += np.einsum('ik,jik->ij',B[0],mu[:,gg[0],:])
    else:
      y_hat += np.einsum('ik,jik->ij', B[0],self.fit['beta_1'][:,gg[0],:])

    if 1 in marginalize:
      y_hat += (np.einsum('ik,jlk->ij', B[1],self.fit['beta_2']) /
                self.fit['beta_2'].shape[1])
    elif 1 in randomize:
      z_2 = np.random.normal(gg[1].unique(),self.fit['z_2'].shape[1])
      beta_2 = np.einsum('ij,ijk,hj->ihj',self.fit['tau_2'],
                         self.fit['L_Omega_2'],z_2)
      y_hat += np.einsum('ij,jik->ij',B[1],beta_2[:,gg[1],:])
    elif len(B) >= 2:
      y_hat += np.einsum('ik,jik->ij', B[1],self.fit['beta_2'][:,gg[1],:])

    if 2 in marginalize:
      y_hat += (np.einsum('ik,jlk->ij', B[2],self.fit['beta_3']) /
                self.fit['beta_3'].shape[2])
    elif 2 in randomize:
      z_3 = np.random.normal(gg[2].unique(),self.fit['z_3'].shape[1])
      beta_3 = np.einsum('ij,ijk,hj->ihj',self.fit['tau_3'],
                         self.fit['L_Omega_3'],z_3)
      y_hat += np.einsum('ij,jik->ij',B[2],beta_3[:,gg[2],:])
    elif len(B) >= 3:
      y_hat += np.einsum('ik,jik->ij', B[2],self.fit['beta_3'][:,gg[2],:])

    if 3 in marginalize:
      y_hat += (np.einsum('ik,jlk->ij', B[3],self.fit['beta_4']) /
                self.fit['beta_4'].shape[2])
    elif 3 in randomize:
      z_4 = np.random.normal(gg[3].unique(),self.fit['z_4'].shape[1])
      beta_4 = np.einsum('ij,ijk,hj->ihj',self.fit['tau_4'],
                         self.fit['L_Omega_4'],z_4)
      y_hat += np.einsum('ij,jik->ij',B[3],beta_4[:,gg[3],:])
    elif len(B) >= 3:
      y_hat += np.einsum('ik,jik->ij', B[3],self.fit['beta_4'][:,gg[3],:])

    if 4 in marginalize:
      y_hat += (np.einsum('ik,jlk->ij', B[4],self.fit['beta_5']) /
                self.fit['beta_5'].shape[2])
    elif 4 in randomize:
      z_5 = np.random.normal(gg[4].unique(),self.fit['z_5'].shape[1])
      beta_5 = np.einsum('ij,ijk,hj->ihj',self.fit['tau_5'],
                         self.fit['L_Omega_5'],z_5)
      y_hat += np.einsum('ij,jik->ij',B[4],beta_5[:,gg[4],:])
    elif len(B) >= 4:
      y_hat += np.einsum('ik,jik->ij', B[4],self.fit['beta_5'][:,gg[4],:])

    if use_dataframe:
      dfp = df.copy()
      dfp = dfp.iloc[np.repeat(np.arange(y_hat.shape[0]),y_hat.shape[1]),:]
      dfp['sample'] = np.tile(np.arange(y_hat.shape[1]),y_hat.shape[0])
      dfp['y_hat'] = np.reshape(y_hat,y_hat.shape[0]*y_hat.shape[1])
      return dfp
    else:
      return y_hat

  def replicate(self,df,randomize=[],N=500):

    return y_hat[:,samples]

  def validate(self,stats=default_stats,N=500,randomize=[],return_samples=False):
    samples = np.random.choice(self.fit['beta_1'].shape[0],size=N,replace=False)
    y_hat = self.predict(randomize=randomize)

    real_diff = self.y[:,np.newaxis] - y_hat[:,samples]
    if not self.robust:
      fake_diff = np.random.normal(0,self.fit['sigma'][np.newaxis,samples],
                                   size=(self.df.shape[0],len(samples)))
    else:
      cauchy = np.random.standard_cauchy
      fake_diff = (cauchy(size=(self.df.shape[0],len(samples))) *
                   self.fit['sigma'][np.newaxis,samples])

    tests = ppp_T(real_diff,fake_diff,stats)

    g = tests.groupby('type')
    summary = g.mean()
    summary['p_val'] = g.apply(lambda d: p_value(d.real - d.fake))
    summary['fakeSE'] = g.fake.std()
    summary['realSE'] = g.real.std()
    if not return_samples:
      return summary
    else:
      return tests

  def log_posterior(self,y=None,df=None):
    if df is None:
      df = self.df.ix[self.A.index]
      y = self.y

    y_hat = self.predict(df)
    y = y[:,np.newaxis]
    if not self.robust:
      lp = scipy.stats.normal(y[:,np.newaxis],y_hat,self.fit['sigma'][np.newaxis,:])
    else:
      lp = scipy.stats.cauchy.pdf(y[:,np.newaxis],y_hat,self.fit['sigma'][np.newaxis,:])

    return lp

  def WAIC(self):
    log_post = self.log_posterior()
    p_waic = np.std(log_post,axis=1,ddof=1)
    lpd = scipy.misc.logsumexp(log_post,axis=1) - np.log(log_post.shape[1])

    waic = -2*np.sum(lpd - p_waic)
    sd = 2*np.sqrt(lpd.shape[0] * np.std(lpd - p_waic))
    return waic,sd,np.sum(p_waic)

  def sample(self,mean_init=0,iters=5,warmup=2,chains=1,**kwds):
    model_input = {"y": self.y,
                   "A": self.A, "n": len(self.y),
                   "k": self.A.shape[1],
                   "B_1": self.B[0].ix[self.A.index],
                   "h_1": self.B[0].shape[1],
                   "gg_1": self.gg[0][self.A.index]+1,
                   "G_1": self.G, "l_1": self.G.shape[1],
                   "g_1": self.G.shape[0],

                   "fixed_mean_prior": self.fixed_prior,
                   "prediction_error_prior": self.eps_prior,

                   "group1_mean_prior": self.groups[0]['mean_prior'],
                   "group1_var_prior": self.groups[0]['var_prior'],
                   "group1_cor_prior": self.groups[0]['cor_prior']}

    # if self.A.shape[1] == 0:
    #   del model_input["A"]

    if len(self.groups) >= 2:
      model_input["B_2"] = self.B[1].ix[self.A.index]
      model_input["h_2"] = self.B[1].shape[1]
      model_input["gg_2"] = self.gg[1][self.A.index]+1
      model_input["g_2"] = self.gdf[1].shape[0]
      model_input["group2_var_prior"] = self.groups[1]['var_prior']
      model_input["group2_cor_prior"] = self.groups[1]['cor_prior']

    if len(self.groups) >= 3:
      model_input["B_3"] = self.B[2].ix[self.A.index]
      model_input["h_3"] = self.B[2].shape[1]
      model_input["gg_3"] = self.gg[2][self.A.index]+1
      model_input["g_3"] = self.gdf[2].shape[0]
      model_input["group3_var_prior"] = self.groups[2]['var_prior']
      model_input["group3_cor_prior"] = self.groups[2]['cor_prior']

    if len(self.groups) >= 4:
      model_input["B_4"] = self.B[3].ix[self.A.index]
      model_input["h_4"] = self.B[3].shape[1]
      model_input["gg_4"] = self.gg[3][self.A.index]+1
      model_input["g_4"] = self.gdf[3].shape[0]
      model_input["group4_var_prior"] = self.groups[3]['var_prior']
      model_input["group4_cor_prior"] = self.groups[3]['cor_prior']

    if len(self.groups) == 5:
      model_input["B_5"] = self.B[4].ix[self.A.index]
      model_input["h_5"] = self.B[4].shape[1]
      model_input["gg_5"] = self.gg[4][self.A.index]+1
      model_input["g_5"] = self.gdf[4].shape[0]
      model_input["group5_var_prior"] = self.groups[4]['var_prior']
      model_input["group5_cor_prior"] = self.groups[4]['cor_prior']

    def init_fn():
      g_1,l_1 = self.G.shape
      h_1 = self.B[0].shape[1]
      if len(self.groups) >= 2:
        g_2 = self.gdf[1].shape[0]
        h_2 = self.B[1].shape[1]
      if len(self.groups) >= 3:
        g_3 = self.gdf[2].shape[0]
        h_3 = self.B[2].shape[1]
      if len(self.groups) >= 4:
        g_4 = self.gdf[3].shape[0]
        h_4 = self.B[3].shape[1]
      if len(self.groups) == 5:
        g_5 = self.gdf[4].shape[0]
        h_5 = self.B[4].shape[1]

      model_init = {"gamma_1": np.random.rand(l_1,h_1)*0.001,
                    "z_1": np.random.rand(h_1,g_1)+0.001,
                    "L_Omega_1": np.zeros((h_1,h_1)),
                    "tau_1": np.random.rand(h_1)+0.001,
                    "alpha": mean_init+np.random.rand()*0.001}

      if self.A.shape[1] == 0:
        del model_init['alpha']

      if len(self.groups) >= 2:
        model_init["z_2"] = np.random.rand(h_2,g_2)+0.001
        model_init["L_Omega_2"] = np.zeros((h_2,h_2))
        model_init["tau_2"] = np.random.rand(h_2)+0.001
      if len(self.groups) >= 3:
        model_init["z_3"] = np.random.rand(h_3,g_3)+0.001
        model_init["L_Omega_3"] = np.zeros((h_3,h_3))
        model_init["tau_3"] = np.random.rand(h_2)+0.001
      if len(self.groups) >= 4:
        model_init["z_4"] = np.random.rand(h_4,g_4)+0.001
        model_init["L_Omega_4"] = np.zeros((h_4,h_4))
        model_init["tau_4"] = np.random.rand(h_4)+0.001
      if len(self.groups) >= 5:
        model_init["z_5"] = np.random.rand(h_5,g_5)+0.001
        model_init["L_Omega_5"] = np.zeros((h_5,h_5))
        model_init["tau_5"] = np.random.rand(h_5)+0.001

      model_init["sigma"] = self.eps_prior+np.random.rand()*0.001

      return model_init

    if len(self.groups) == 1:
      if self.robust:
          RuntimeError("Not implemented!")
      fit = model1.sampling(data=model_input,init=init_fn,iter=iters,
                            chains=chains,warmup=warmup,**kwds)
    if len(self.groups) == 2:
      if not self.robust:
        if self.A.shape[1] == 0:
          fit = model2_nf.sampling(data=model_input,iter=iters,
                                   chains=chains,warmup=warmup,**kwds)
        else:
          fit = model2.sampling(data=model_input,iter=iters,
                                chains=chains,warmup=warmup,**kwds)

      else:
        fit = rmodel2.sampling(data=model_input,init=init_fn,iter=iters,
                               chains=chains,warmup=warmup,**kwds)
    if len(self.groups) == 3:
      if self.robust:
          RuntimeError("Not implemented!")
      fit = model3.sampling(data=model_input,init=init_fn,iter=iters,
                            chains=chains,warmup=warmup,**kwds)
    if len(self.groups) == 4:
      if self.robust:
          RuntimeError("Not implemented!")
      fit = model4.sampling(data=model_input,init=init_fn,iter=iters,
                            chains=chains,warmup=warmup,**kwds)

    if len(self.groups) == 5:
      if self.robust:
          RuntimeError("Not implemented!")
      fit = model5.sampling(data=model_input,init=init_fn,iter=iters,
                            chains=chains,warmup=warmup,**kwds)

    self.fit = fit
    return self
