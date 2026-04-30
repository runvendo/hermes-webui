const ONBOARDING={status:null,step:0,steps:['system','setup','workspace','password','finish'],form:{provider:'openrouter',workspace:'',model:'',password:'',apiKey:'',baseUrl:''},active:false,_vendoSetupUnsubscribe:null};

function _isVendoActive(){
  return !!(ONBOARDING && ONBOARDING.status && ONBOARDING.status.vendo && ONBOARDING.status.vendo.active);
}

function _getOnboardingSetupProviders(){
  return (((ONBOARDING.status||{}).setup||{}).providers)||[];
}

function _getOnboardingSetupProvider(id){
  return _getOnboardingSetupProviders().find(p=>p.id===id)||null;
}

function _getOnboardingSetupCategories(){
  return (((ONBOARDING.status||{}).setup||{}).categories)||[];
}

/** Render the provider <select> with <optgroup> per category. */
function _renderProviderSelectOptions(selectedId){
  const providers=_getOnboardingSetupProviders();
  const categories=_getOnboardingSetupCategories();
  const provMap={};
  providers.forEach(p=>{provMap[p.id]=p;});
  if(!categories.length){
    // Fallback: flat list when no categories are available.
    return providers.map(p=>`<option value="${esc(p.id)}">${esc(p.label)}${p.quick?' — '+esc(t('onboarding_quick_setup_badge')):''}</option>`).join('');
  }
  return categories.map(cat=>{
    const opts=cat.providers.map(pid=>{
      const p=provMap[pid];
      if(!p)return '';
      return `<option value="${esc(p.id)}"${p.id===selectedId?' selected':''}>${esc(p.label)}${p.quick?' — '+esc(t('onboarding_quick_setup_badge')):''}</option>`;
    }).join('');
    return `<optgroup label="${esc(t('provider_category_'+cat.id)||cat.label)}">${opts}</optgroup>`;
  }).join('');
}

function _getOnboardingCurrentSetup(){
  return (((ONBOARDING.status||{}).setup||{}).current)||{};
}

function _onboardingStepMeta(key){
  const vendoActive=_isVendoActive();
  const map={
    system:vendoActive
      ?{title:'Vendo connection',desc:'Verify identity, connections, and Vendo API.'}
      :{title:t('onboarding_step_system_title'),desc:t('onboarding_step_system_desc')},
    setup:vendoActive
      ?{title:'Providers and integrations',desc:'Confirm what Vendo has connected for you.'}
      :{title:t('onboarding_step_setup_title'),desc:t('onboarding_step_setup_desc')},
    // Vendo-only steps — the non-Vendo flow uses "setup" above.
    providers:{title:'Providers',desc:'AI models routed through Vendo.'},
    connections:{title:'Connections',desc:'Integrations like Telegram and Notion.'},
    workspace:{title:t('onboarding_step_workspace_title'),desc:t('onboarding_step_workspace_desc')},
    password:{title:t('onboarding_step_password_title'),desc:t('onboarding_step_password_desc')},
    finish:vendoActive
      ?{title:t('onboarding_step_finish_title'),desc:'Connected via Vendo. Open chat to start.'}
      :{title:t('onboarding_step_finish_title'),desc:t('onboarding_step_finish_desc')}
  };
  return map[key]||{title:key,desc:''};
}

function _renderOnboardingSteps(){
  const wrap=$('onboardingSteps');
  if(!wrap)return;
  wrap.innerHTML='';
  ONBOARDING.steps.forEach((key,idx)=>{
    const meta=_onboardingStepMeta(key);
    const item=document.createElement('div');
    item.className='onboarding-step'+(idx===ONBOARDING.step?' active':idx<ONBOARDING.step?' done':'');
    item.innerHTML=`<div class="onboarding-step-index">${idx+1}</div><div><div class="onboarding-step-title">${meta.title}</div><div class="onboarding-step-desc">${meta.desc}</div></div>`;
    wrap.appendChild(item);
  });
}

function _setOnboardingNotice(msg,kind='info'){
  const el=$('onboardingNotice');
  if(!el)return;
  if(!msg){el.style.display='none';el.textContent='';el.className='onboarding-status';return;}
  el.style.display='block';
  el.className='onboarding-status '+kind;
  el.textContent=msg;
}

function _getOnboardingWorkspaceChoices(){
  const items=((ONBOARDING.status||{}).workspaces||{}).items||[];
  return items.length?items:[{name:'Home',path:ONBOARDING.form.workspace||''}];
}

function _getOnboardingProviderModelChoices(){
  const provider=_getOnboardingSetupProvider(ONBOARDING.form.provider);
  return provider?(provider.models||[]):[];
}

function _getOnboardingSelectedModel(){
  return ONBOARDING.form.model||'';
}

function _renderOnboardingModelField(){
  const choices=_getOnboardingProviderModelChoices();
  if(ONBOARDING.form.provider==='custom'){
    return `<label class="onboarding-field"><span>${t('onboarding_model_label')}</span><input id="onboardingModelInput" value="${esc(_getOnboardingSelectedModel())}" placeholder="${t('onboarding_custom_model_placeholder')}" oninput="ONBOARDING.form.model=this.value"></label><p class="onboarding-copy">${t('onboarding_custom_model_help')}</p>`;
  }
  const options=choices.map(m=>`<option value="${esc(m.id)}">${esc(m.label)}</option>`).join('');
  return `<label class="onboarding-field"><span>${t('onboarding_model_label')}</span><select id="onboardingModelSelect" onchange="ONBOARDING.form.model=this.value">${options}</select></label><p class="onboarding-copy">${t('onboarding_workspace_help')}</p>`;
}

function _providerStatusLabel(system){
  if(system.chat_ready) return t('onboarding_check_provider_ready');
  if(system.provider_configured) return t('onboarding_check_provider_partial');
  return t('onboarding_check_provider_pending');
}

function _renderOnboardingBody(){
  const body=$('onboardingBody');
  if(!body||!ONBOARDING.status)return;
  const key=ONBOARDING.steps[ONBOARDING.step];
  const system=ONBOARDING.status.system||{};
  const settings=ONBOARDING.status.settings||{};
  const setup=ONBOARDING.status.setup||{};
  const nextBtn=$('onboardingNextBtn');
  const backBtn=$('onboardingBackBtn');
  if(backBtn) backBtn.style.display=ONBOARDING.step>0?'':'none';
  if(nextBtn) nextBtn.textContent=key==='finish'?t('onboarding_open'):t('onboarding_continue');

  if(key==='system'){
    if(_isVendoActive()){
      _renderVendoSystemPane(body, ONBOARDING.status.vendo);
      return;
    }
    const hermesOk=system.hermes_found&&system.imports_ok;
    const setupOk=!!system.chat_ready;
    _setOnboardingNotice(system.provider_note|| (setupOk?t('onboarding_notice_system_ready'):t('onboarding_notice_system_unavailable')),setupOk?'success':(hermesOk?'info':'warn'));
    body.innerHTML=`
      <div class="onboarding-panel-grid">
        <div class="onboarding-check ${hermesOk?'ok':'warn'}"><strong>${t('onboarding_check_agent')}</strong><span>${hermesOk?t('onboarding_check_agent_ready'):t('onboarding_check_agent_missing')}</span></div>
        <div class="onboarding-check ${(setupOk?'ok':system.provider_configured?'warn':'muted')}"><strong>${t('onboarding_check_provider')}</strong><span>${_providerStatusLabel(system)}</span></div>
        <div class="onboarding-check ${(settings.password_enabled?'ok':'muted')}"><strong>${t('onboarding_check_password')}</strong><span>${settings.password_enabled?t('onboarding_check_password_enabled'):t('onboarding_check_password_disabled')}</span></div>
      </div>
      <div class="onboarding-copy">
        <p><strong>${t('onboarding_config_file')}</strong> ${esc(system.config_path||t('onboarding_unknown'))}</p>
        <p><strong>${t('onboarding_env_file')}</strong> ${esc(system.env_path||t('onboarding_unknown'))}</p>
        <p>${esc(system.provider_note||'')}</p>
        ${system.current_provider?`<p><strong>${t('onboarding_current_provider')}</strong> ${esc(system.current_provider)}${system.current_model?` — ${esc(system.current_model)}`:''}</p>`:''}
        ${system.current_base_url?`<p><strong>${t('onboarding_base_url_label')}</strong> ${esc(system.current_base_url)}</p>`:''}
        ${system.missing_modules&&system.missing_modules.length?`<p><strong>${t('onboarding_missing_imports')}</strong> ${esc(system.missing_modules.join(', '))}</p>`:''}
      </div>`;
    return;
  }

  if(key==='providers' && _isVendoActive()){
    _renderVendoProvidersPane(body);
    return;
  }

  if(key==='connections' && _isVendoActive()){
    _renderVendoConnectionsPane(body);
    return;
  }

  if(key==='setup'){
    if(_isVendoActive()){
      _renderVendoSetupPane(body);
      return;
    }
    const selectedId=ONBOARDING.form.provider;
    const groupedOptions=_renderProviderSelectOptions(selectedId);
    const provider=_getOnboardingSetupProvider(selectedId)||_getOnboardingSetupProviders()[0]||null;
    const showBaseUrl=provider&&provider.requires_base_url;
    const keyHelp=provider?`${t('onboarding_api_key_help_prefix')} ${esc(provider.env_var)}.`:'';

    // OAuth provider path: configured via CLI, no API key input needed.
    const currentIsOauth=!!(ONBOARDING.status.setup||{}).current_is_oauth;
    const currentProviderName=((ONBOARDING.status.setup||{}).current||{}).provider||'';
    if(currentIsOauth){
      const isReady=!!(ONBOARDING.status.system||{}).chat_ready;
      const providerLabel=esc(currentProviderName);
      if(isReady){
        _setOnboardingNotice(t('onboarding_notice_setup_already_ready'),'success');
        body.innerHTML=`
          <div class="onboarding-oauth-card onboarding-oauth-ready">
            <div class="onboarding-oauth-icon">✓</div>
            <div>
              <strong>${t('onboarding_oauth_provider_ready_title')}</strong>
              <p>${t('onboarding_oauth_provider_ready_body').replace('{provider}',providerLabel)}</p>
            </div>
          </div>
          <p class="onboarding-copy" style="margin-top:20px">${t('onboarding_oauth_switch_hint')}</p>
          <label class="onboarding-field">
            <span>${t('onboarding_provider_label')}</span>
            <select id="onboardingProviderSelect" onchange="syncOnboardingProvider(this.value)">${groupedOptions}</select>
          </label>
          <label class="onboarding-field" id="onboardingApiKeyField">
            <span>${t('onboarding_api_key_label')}</span>
            <input id="onboardingApiKeyInput" type="password" value="${esc(ONBOARDING.form.apiKey||'')}" placeholder="${t('onboarding_api_key_placeholder')}" oninput="ONBOARDING.form.apiKey=this.value">
          </label>
          ${showBaseUrl?`<label class="onboarding-field"><span>${t('onboarding_base_url_label')}</span><input id="onboardingBaseUrlInput" value="${esc(ONBOARDING.form.baseUrl||'')}" placeholder="${t('onboarding_base_url_placeholder')}" oninput="ONBOARDING.form.baseUrl=this.value"></label>`:''}
          <p class="onboarding-copy">${keyHelp}</p>`;
      } else {
        _setOnboardingNotice(t('onboarding_notice_setup_required'),'warn');
        body.innerHTML=`
          <div class="onboarding-oauth-card onboarding-oauth-pending">
            <div class="onboarding-oauth-icon">⚠</div>
            <div>
              <strong>${t('onboarding_oauth_provider_not_ready_title')}</strong>
              <p>${t('onboarding_oauth_provider_not_ready_body').replace('{provider}',providerLabel)}</p>
            </div>
          </div>
          <p class="onboarding-copy" style="margin-top:20px">${t('onboarding_oauth_switch_hint')}</p>
          <label class="onboarding-field">
            <span>${t('onboarding_provider_label')}</span>
            <select id="onboardingProviderSelect" onchange="syncOnboardingProvider(this.value)">${groupedOptions}</select>
          </label>
          <label class="onboarding-field" id="onboardingApiKeyField">
            <span>${t('onboarding_api_key_label')}</span>
            <input id="onboardingApiKeyInput" type="password" value="${esc(ONBOARDING.form.apiKey||'')}" placeholder="${t('onboarding_api_key_placeholder')}" oninput="ONBOARDING.form.apiKey=this.value">
          </label>
          ${showBaseUrl?`<label class="onboarding-field"><span>${t('onboarding_base_url_label')}</span><input id="onboardingBaseUrlInput" value="${esc(ONBOARDING.form.baseUrl||'')}" placeholder="${t('onboarding_base_url_placeholder')}" oninput="ONBOARDING.form.baseUrl=this.value"></label>`:''}
          <p class="onboarding-copy">${keyHelp}</p>`;
      }
      return;
    }

    _setOnboardingNotice(system.chat_ready?t('onboarding_notice_setup_already_ready'):t('onboarding_notice_setup_required'),system.chat_ready?'success':'info');
    body.innerHTML=`
      <label class="onboarding-field">
        <span>${t('onboarding_provider_label')}</span>
        <select id="onboardingProviderSelect" onchange="syncOnboardingProvider(this.value)">${groupedOptions}</select>
      </label>
      <label class="onboarding-field">
        <span>${t('onboarding_api_key_label')}</span>
        <input id="onboardingApiKeyInput" type="password" value="${esc(ONBOARDING.form.apiKey||'')}" placeholder="${t('onboarding_api_key_placeholder')}" oninput="ONBOARDING.form.apiKey=this.value">
      </label>
      ${showBaseUrl?`<label class="onboarding-field"><span>${t('onboarding_base_url_label')}</span><input id="onboardingBaseUrlInput" value="${esc(ONBOARDING.form.baseUrl||'')}" placeholder="${t('onboarding_base_url_placeholder')}" oninput="ONBOARDING.form.baseUrl=this.value"></label>`:''}
      <p class="onboarding-copy">${keyHelp}</p>
      ${showBaseUrl?`<p class="onboarding-copy">${t('onboarding_base_url_help')}</p>`:''}
      <p class="onboarding-copy">${esc(setup.unsupported_note||'')||''}</p>`;
    return;
  }

  if(key==='workspace'){
    const workspaceOptions=_getOnboardingWorkspaceChoices().map(ws=>`<option value="${esc(ws.path)}">${esc(ws.name||ws.path)} — ${esc(ws.path)}</option>`).join('');
    _setOnboardingNotice(t('onboarding_notice_workspace'), 'info');
    body.innerHTML=`
      <label class="onboarding-field">
        <span>${t('onboarding_workspace_label')}</span>
        <select id="onboardingWorkspaceSelect" onchange="syncOnboardingWorkspaceSelect(this.value)">${workspaceOptions}</select>
      </label>
      <label class="onboarding-field">
        <span>${t('onboarding_workspace_or_path')}</span>
        <input id="onboardingWorkspaceInput" value="${esc(ONBOARDING.form.workspace||'')}" placeholder="${t('onboarding_workspace_placeholder')}" oninput="ONBOARDING.form.workspace=this.value">
      </label>
      ${_renderOnboardingModelField()}`;
    const wsSel=$('onboardingWorkspaceSelect');
    if(wsSel && ONBOARDING.form.workspace) wsSel.value=ONBOARDING.form.workspace;
    const modelSel=$('onboardingModelSelect');
    if(modelSel && ONBOARDING.form.model) modelSel.value=ONBOARDING.form.model;
    return;
  }

  if(key==='password'){
    _setOnboardingNotice(settings.password_enabled?t('onboarding_notice_password_enabled'):t('onboarding_notice_password_recommended'), settings.password_enabled?'success':'info');
    body.innerHTML=`
      <label class="onboarding-field">
        <span>${t('onboarding_password_label')}</span>
        <input id="onboardingPasswordInput" type="password" value="${esc(ONBOARDING.form.password||'')}" placeholder="${t('onboarding_password_placeholder')}" oninput="ONBOARDING.form.password=this.value">
      </label>
      <p class="onboarding-copy">${t('onboarding_password_help')}</p>`;
    return;
  }

  if(_isVendoActive()){
    const vendo=ONBOARDING.status.vendo||{};
    const slugs=(vendo.connections&&vendo.connections.connected_slugs)||[];
    const ident=vendo.identity||{};
    const greetingName=esc(ident.name || (ident.email?ident.email.split('@')[0]:'') || 'there');
    _setOnboardingNotice('', null);  // suppress the top notice; the finish hero replaces it
    body.innerHTML=`
      <div class="onboarding-finish-hero">
        <div class="onboarding-finish-mark"><span>V</span></div>
        <h2 class="onboarding-finish-title">You're all set</h2>
        <p class="onboarding-finish-sub">Hermes is ready, signed in via Vendo.</p>
      </div>
      <div class="onboarding-summary onboarding-finish-summary">
        <div><strong>Identity</strong><span>${esc(ident.name || ident.email || 'Vendo user')}</span></div>
        <div><strong>Connections</strong><span>${esc(slugs.length?slugs.join(', '):'None yet')}</span></div>
        <div><strong>Workspace</strong><span>${esc(ONBOARDING.form.workspace || t('onboarding_not_set'))}</span></div>
        <div><strong>Default model</strong><span>${esc(_getOnboardingSelectedModel() || t('onboarding_not_set'))}</span></div>
      </div>
      <p class="onboarding-copy">Manage providers and integrations anytime from <a href="https://vendo.run/dashboard" target="_blank" rel="noopener">vendo.run/dashboard</a>.</p>`;
    return;
  }

  const provider=_getOnboardingSetupProvider(ONBOARDING.form.provider);
  _setOnboardingNotice(t('onboarding_notice_finish'), 'success');
  body.innerHTML=`
    <div class="onboarding-summary">
      <div><strong>${t('onboarding_provider_label')}</strong><span>${esc((provider&&provider.label)||ONBOARDING.form.provider||t('onboarding_not_set'))}</span></div>
      <div><strong>${t('onboarding_model_label')}</strong><span>${esc(_getOnboardingSelectedModel()||t('onboarding_not_set'))}</span></div>
      <div><strong>${t('onboarding_workspace_label')}</strong><span>${esc(ONBOARDING.form.workspace||t('onboarding_not_set'))}</span></div>
      <div><strong>${t('onboarding_check_password')}</strong><span>${t(_getOnboardingPasswordSummaryKey(settings))}</span></div>
    </div>
    ${ONBOARDING.form.baseUrl?`<p class="onboarding-copy"><strong>${t('onboarding_base_url_label')}</strong> ${esc(ONBOARDING.form.baseUrl)}</p>`:''}
    <p class="onboarding-copy">${t('onboarding_finish_help')}</p>`;
}

function _getOnboardingPasswordSummaryKey(settings){
  const hasExistingPassword=!!(settings&&settings.password_enabled);
  const hasNewPassword=!!((ONBOARDING.form.password||'').trim());
  if(hasNewPassword) return hasExistingPassword?'onboarding_password_will_replace':'onboarding_password_will_enable';
  return hasExistingPassword?'onboarding_password_keep_existing':'onboarding_password_remains_disabled';
}

function syncOnboardingWorkspaceSelect(value){
  ONBOARDING.form.workspace=value;
  const input=$('onboardingWorkspaceInput');
  if(input) input.value=value;
}

function syncOnboardingProvider(value){
  const provider=_getOnboardingSetupProvider(value);
  ONBOARDING.form.provider=value;
  if(provider){
    if(!ONBOARDING.form.model || !_getOnboardingProviderModelChoices().some(m=>m.id===ONBOARDING.form.model) || value==='custom'){
      ONBOARDING.form.model=provider.default_model||'';
    }
    if(provider.requires_base_url){
      ONBOARDING.form.baseUrl=ONBOARDING.form.baseUrl||provider.default_base_url||'';
    }else{
      ONBOARDING.form.baseUrl=provider.default_base_url||'';
    }
  }
  _renderOnboardingBody();
}

function _renderVendoSystemPane(body, vendo){
  const identity=vendo&&vendo.identity;
  const conns=(vendo&&vendo.connections)||{};
  const identityOk=!!identity;
  const connsOk=!!conns.available;
  const liveApi=!!conns.live_api;

  const allOk=identityOk&&connsOk&&liveApi;
  _setOnboardingNotice(allOk?'Vendo connection verified.':'Some Vendo signals are missing.', allOk?'success':'info');

  const tile=(label,ok,sub)=>`
    <div class="onboarding-check ${ok?'ok':'warn'}">
      <strong>${esc(label)}</strong>
      <span>${esc(sub)}</span>
    </div>`;

  const identitySub=identityOk
    ? `Connected as ${identity.name||identity.email||identity.user_id||'Vendo user'}`
    : 'Not signed in to Vendo';
  const connectedSlugs=conns.connected_slugs||[];
  const connsSub=connsOk
    ? `${connectedSlugs.length} connected${connectedSlugs.length?': '+connectedSlugs.join(', '):''}`
    : 'No connections yet';
  const apiSub=liveApi?'Reachable':'Using cached state';

  body.innerHTML=`
    <div class="onboarding-panel-grid">
      ${tile('Identity', identityOk, identitySub)}
      ${tile('Connections', connsOk, connsSub)}
      ${tile('Vendo API', liveApi, apiSub)}
    </div>
    <div class="onboarding-copy">
      <p>Vendo manages identity, billing, and connections for this deployment. You can manage them anytime from <a href="https://vendo.run/dashboard" target="_blank" rel="noopener">vendo.run/dashboard</a>.</p>
    </div>`;
}

function _teardownVendoSetupSubscription(){
  if(ONBOARDING._vendoSetupUnsubscribe){
    try{ ONBOARDING._vendoSetupUnsubscribe(); }
    catch(e){ console.warn('[onboarding] vendo unsubscribe threw', e); }
    ONBOARDING._vendoSetupUnsubscribe=null;
  }
}

/**
 * Render a filtered Vendo cards pane. Subscribes to VendoConnections and
 * re-paints the container on every callback. Stores the unsubscribe in
 * ONBOARDING._vendoSetupUnsubscribe so the existing teardown helper handles
 * both providers and connections steps.
 *
 * @param {HTMLElement} body          — wizard body to populate
 * @param {Object}       opts
 * @param {(c)=>boolean} opts.filter  — predicate over a connection card
 * @param {string}       opts.notice  — banner text shown above the list
 * @param {string}       opts.empty   — message when the filter yields nothing
 * @param {string}       opts.header  — header above the card list
 * @param {boolean}      opts.byok    — whether to append the collapsed BYOK details
 */
function _renderVendoCardsPane(body, opts){
  _teardownVendoSetupSubscription();
  _setOnboardingNotice(opts.notice, 'info');

  if(!window.VendoConnections){
    body.innerHTML='<div class="onboarding-status warn">Connections module not loaded</div>';
    return;
  }

  body.innerHTML='<div id="onboardingVendoSetup" class="onboarding-vendo-setup"></div>';
  const container=$('onboardingVendoSetup');

  ONBOARDING._vendoSetupUnsubscribe=window.VendoConnections.subscribe((connections, fetchError)=>{
    if(!container.isConnected) return;  // step changed; ignore stale callback
    container.innerHTML='';

    if(connections===null){
      const spinner=document.createElement('div');
      spinner.className='integrations-loading';
      spinner.innerHTML='<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9" stroke-dasharray="40" stroke-dashoffset="20" stroke-linecap="round"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></circle></svg>';
      container.appendChild(spinner);
      return;
    }

    if(fetchError){
      const err=document.createElement('div');
      err.className='onboarding-status warn';
      err.textContent="Couldn't reach Vendo: "+fetchError;
      container.appendChild(err);
      return;
    }

    const filtered=(connections||[]).filter(opts.filter);
    if(filtered.length){
      const section=document.createElement('div');
      section.className='onboarding-conn-section';
      section.innerHTML=`<div class="onboarding-conn-header">${esc(opts.header)}</div>`;
      for(const c of filtered){
        if(typeof _buildIntegrationCard==='function') section.appendChild(_buildIntegrationCard(c));
      }
      container.appendChild(section);
    } else {
      const empty=document.createElement('div');
      empty.className='onboarding-copy';
      empty.innerHTML=opts.empty;
      const link=empty.querySelector('a[data-onboarding-jump-integrations]');
      if(link) link.addEventListener('click', (ev)=>{ ev.preventDefault(); if(typeof switchSettingsSection==='function') switchSettingsSection('integrations'); });
      container.appendChild(empty);
    }

    if(opts.byok){
      const byok=document.createElement('details');
      byok.className='onboarding-byok';
      byok.innerHTML='<summary>Use your own API keys (advanced)</summary><p class="onboarding-copy">Hermes also supports your own provider keys. After onboarding, open Settings → Providers to add them — Vendo-managed keys will still take priority.</p>';
      container.appendChild(byok);
    }
  });
}

function _renderVendoProvidersPane(body){
  _renderVendoCardsPane(body, {
    filter: c => c.category === 'ai',
    notice: 'AI providers are managed by Vendo.',
    header: 'AI providers (Vendo-managed)',
    empty: 'No AI providers connected yet. Connect one in <a href="https://vendo.run/dashboard" target="_blank" rel="noopener">vendo.run/dashboard</a>.',
    byok: true,
  });
}

function _renderVendoConnectionsPane(body){
  _renderVendoCardsPane(body, {
    filter: c => c.category !== 'ai',
    notice: 'Optional integrations like Telegram and Notion. You can skip and add these later.',
    header: 'Integrations',
    empty: 'No integrations available right now. You can add them later from <a href="#" data-onboarding-jump-integrations="1">Settings → Integrations</a>.',
    byok: false,
  });
}

function _renderVendoSetupPane(body){
  // Legacy single-pane render — kept for compatibility if a deployment ever
  // surfaces the combined "setup" step under SSO. The split flow uses
  // _renderVendoProvidersPane + _renderVendoConnectionsPane.
  _teardownVendoSetupSubscription();
  _setOnboardingNotice('Vendo manages your AI providers and integrations.', 'info');

  if(!window.VendoConnections){
    body.innerHTML='<div class="onboarding-status warn">Connections module not loaded</div>';
    return;
  }

  body.innerHTML='<div id="onboardingVendoSetup" class="onboarding-vendo-setup"></div>';
  const container=$('onboardingVendoSetup');

  ONBOARDING._vendoSetupUnsubscribe=window.VendoConnections.subscribe((connections, fetchError)=>{
    if(!container.isConnected) return;
    container.innerHTML='';

    if(connections===null){
      const spinner=document.createElement('div');
      spinner.className='integrations-loading';
      spinner.innerHTML='<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9" stroke-dasharray="40" stroke-dashoffset="20" stroke-linecap="round"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></circle></svg>';
      container.appendChild(spinner);
      return;
    }

    if(fetchError){
      const err=document.createElement('div');
      err.className='onboarding-status warn';
      err.textContent="Couldn't reach Vendo: "+fetchError;
      container.appendChild(err);
      return;
    }

    const all=connections||[];
    const ai=all.filter(c=>c.category==='ai');
    const nonAi=all.filter(c=>c.category!=='ai');

    if(ai.length){
      const aiSection=document.createElement('div');
      aiSection.className='onboarding-conn-section';
      aiSection.innerHTML='<div class="onboarding-conn-header">AI providers (Vendo-managed)</div>';
      for(const c of ai){
        if(typeof _buildIntegrationCard==='function') aiSection.appendChild(_buildIntegrationCard(c));
      }
      container.appendChild(aiSection);
    }

    if(nonAi.length){
      const intSection=document.createElement('div');
      intSection.className='onboarding-conn-section';
      intSection.innerHTML='<div class="onboarding-conn-header">Integrations</div>';
      for(const c of nonAi){
        if(typeof _buildIntegrationCard==='function') intSection.appendChild(_buildIntegrationCard(c));
      }
      container.appendChild(intSection);
    }

    if(!all.length){
      const empty=document.createElement('div');
      empty.className='onboarding-copy';
      empty.innerHTML='No connections yet. Add some in <a href="#" data-onboarding-jump-integrations="1">Settings → Integrations</a> after onboarding.';
      const link=empty.querySelector('a[data-onboarding-jump-integrations]');
      if(link) link.addEventListener('click', (ev)=>{ ev.preventDefault(); if(typeof switchSettingsSection==='function') switchSettingsSection('integrations'); });
      container.appendChild(empty);
    }

    const byok=document.createElement('details');
    byok.className='onboarding-byok';
    byok.innerHTML='<summary>Use your own API keys (advanced)</summary><p class="onboarding-copy">Hermes also supports your own provider keys. After onboarding, open Settings → Providers to add them — Vendo-managed keys will still take priority.</p>';
    container.appendChild(byok);
  });
}

function _applyVendoWelcomeOverride(status){
  const titleEl=$('onboardingTitle');
  const leadEl=$('onboardingLead');
  if(!titleEl) return;
  const vendo=status&&status.vendo;
  if(vendo&&vendo.active){
    const ident=vendo.identity||{};
    let displayName=(ident.name||'').trim();
    if(!displayName && ident.email) displayName=String(ident.email).split('@')[0];
    titleEl.textContent=displayName?`Welcome, ${displayName}!`:'Welcome to Hermes via Vendo';
    if(leadEl) leadEl.textContent='Vendo handles auth, billing, and connections. A quick check-in and you’re ready to chat.';
  }
}

async function loadOnboardingWizard(){
  try{
    const status=await api('/api/onboarding/status');
    ONBOARDING.status=status;
    // Honour server-provided step list (e.g. password step is dropped under Vendo SSO).
    if(Array.isArray(status.steps)&&status.steps.length){
      ONBOARDING.steps=status.steps.slice();
    }
    const current=((status.setup||{}).current)||{};
    ONBOARDING.form.provider=current.provider||'openrouter';
    ONBOARDING.form.workspace=(status.workspaces&&status.workspaces.last)||status.settings.default_workspace||'';
    ONBOARDING.form.model=status.settings.default_model||current.model||'';
    ONBOARDING.form.password='';
    ONBOARDING.form.apiKey='';
    ONBOARDING.form.baseUrl=current.base_url||'';
    ONBOARDING.active=!status.completed;
    if(!ONBOARDING.active) return false;
    $('onboardingOverlay').style.display='flex';
    _applyVendoWelcomeOverride(status);
    _renderOnboardingSteps();
    _renderOnboardingBody();
    return true;
  }catch(e){
    console.warn('onboarding status failed',e);
    return false;
  }
}

function prevOnboardingStep(){
  if(ONBOARDING.step===0)return;
  // Leaving setup/providers/connections: drop the Vendo connections subscription.
  const leaving=ONBOARDING.steps[ONBOARDING.step];
  if(leaving==='setup' || leaving==='providers' || leaving==='connections') _teardownVendoSetupSubscription();
  ONBOARDING.step--;
  _renderOnboardingSteps();
  _renderOnboardingBody();
}

async function _saveOnboardingProviderSetup(){
  // Under Vendo SSO, Vendo manages the provider credentials. Don't POST onboarding
  // setup — the local config/.env should not be touched.
  if(_isVendoActive()) return;
  const provider=(ONBOARDING.form.provider||'').trim();
  const model=(ONBOARDING.form.model||'').trim();
  const apiKey=(ONBOARDING.form.apiKey||'').trim();
  const baseUrl=(ONBOARDING.form.baseUrl||'').trim();
  const current=_getOnboardingCurrentSetup();
  const isUnchanged=current.provider===provider&&((current.model||'')===model)&&((current.base_url||'')===baseUrl);
  // Skip the POST when nothing changed.  We also skip when the provider is
  // unsupported/OAuth-based and already working — chat_ready may be false for
  // providers not in the quick-setup list (e.g. minimax-cn) even though they are
  // fully configured.  Posting in that case would either be a no-op (the server
  // just marks complete for unsupported providers) or could silently overwrite
  // config.yaml if the user accidentally changed the provider dropdown.
  const currentIsOauth=!!(ONBOARDING.status&&ONBOARDING.status.setup&&ONBOARDING.status.setup.current_is_oauth);
  if(isUnchanged && !apiKey && ((ONBOARDING.status.system||{}).chat_ready || currentIsOauth)) return;
  const body={provider,model};
  if(apiKey) body.api_key=apiKey;
  if(baseUrl) body.base_url=baseUrl;
  const status=await api('/api/onboarding/setup',{method:'POST',body:JSON.stringify(body)});
  ONBOARDING.status=status;
}

async function _saveOnboardingDefaults(){
  const workspace=(ONBOARDING.form.workspace||'').trim();
  const model=(ONBOARDING.form.model||'').trim();
  const password=(ONBOARDING.form.password||'').trim();
  if(!workspace) throw new Error(t('onboarding_error_choose_workspace'));
  if(!model) throw new Error(t('onboarding_error_choose_model'));
  const known=_getOnboardingWorkspaceChoices().some(ws=>ws.path===workspace);
  if(!known){
    await api('/api/workspaces/add',{method:'POST',body:JSON.stringify({path:workspace})});
  }
  // Model persisted by /api/onboarding/setup — no /api/default-model call needed here
  const body={default_workspace:workspace};
  if(password) body._set_password=password;
  const saved=await api('/api/settings',{method:'POST',body:JSON.stringify(body)});
  if(ONBOARDING.status){
    ONBOARDING.status.settings={...(ONBOARDING.status.settings||{}),password_enabled:!!saved.auth_enabled};
  }
  localStorage.setItem('hermes-webui-model',model);
  if($('modelSelect')) _applyModelToDropdown(model,$('modelSelect'));
}

async function _finishOnboarding(){
  await _saveOnboardingProviderSetup();
  await _saveOnboardingDefaults();
  const done=await api('/api/onboarding/complete',{method:'POST',body:'{}'});
  ONBOARDING.status=done;
  ONBOARDING.active=false;
  _teardownVendoSetupSubscription();
  $('onboardingOverlay').style.display='none';
  showToast(t('onboarding_complete'));
  await loadWorkspaceList();
  if(typeof renderSessionList==='function') await renderSessionList();
  if(!S.session && typeof newSession==='function'){
    await newSession(true);
    await renderSessionList();
  }
}

async function skipOnboarding(){
  try{
    // Mark onboarding completed server-side without changing any config
    await api('/api/onboarding/complete',{method:'POST',body:'{}'});
    ONBOARDING.active=false;
    _teardownVendoSetupSubscription();
    $('onboardingOverlay').style.display='none';
    showToast(t('onboarding_skipped')||'Setup skipped');
  }catch(e){
    _setOnboardingNotice((e.message||String(e)),'warn');
  }
}

async function nextOnboardingStep(){
  try{
    const currentKey=ONBOARDING.steps[ONBOARDING.step];
    if(currentKey==='setup'){
      if(_isVendoActive()){
        // Vendo-managed setup: auto-pass when at least one AI provider is connected.
        // We skip the provider/key form entirely — Vendo owns those credentials.
        const slugs=((ONBOARDING.status.vendo||{}).connections||{}).connected_slugs||[];
        const hasAi=slugs.some(s=>['openrouter','openai','anthropic'].includes(s));
        if(!hasAi) throw new Error('Connect an AI provider in Vendo before continuing.');
        _teardownVendoSetupSubscription();
      } else {
        ONBOARDING.form.provider=(($('onboardingProviderSelect')||{}).value||ONBOARDING.form.provider||'').trim();
        ONBOARDING.form.apiKey=(($('onboardingApiKeyInput')||{}).value||'').trim();
        ONBOARDING.form.baseUrl=(($('onboardingBaseUrlInput')||{}).value||ONBOARDING.form.baseUrl||'').trim();
        if(!ONBOARDING.form.provider) throw new Error(t('onboarding_error_provider_required'));
        if(ONBOARDING.form.provider==='custom' && !ONBOARDING.form.baseUrl) throw new Error(t('onboarding_error_base_url_required'));
      }
    }
    if(currentKey==='providers'){
      // Vendo-only step. Auto-pass when at least one AI provider is connected.
      const slugs=((ONBOARDING.status.vendo||{}).connections||{}).connected_slugs||[];
      const hasAi=slugs.some(s=>['openrouter','openai','anthropic'].includes(s));
      if(!hasAi) throw new Error('Connect an AI provider in Vendo before continuing.');
      _teardownVendoSetupSubscription();
    }
    if(currentKey==='connections'){
      // Vendo-only step. Integrations are optional — always passes.
      _teardownVendoSetupSubscription();
    }
    if(ONBOARDING.steps[ONBOARDING.step]==='workspace'){
      ONBOARDING.form.workspace=(($('onboardingWorkspaceInput')||{}).value||ONBOARDING.form.workspace||'').trim();
      ONBOARDING.form.model=(($('onboardingModelInput')||{}).value||($('onboardingModelSelect')||{}).value||ONBOARDING.form.model||'').trim();
      if(!ONBOARDING.form.workspace) throw new Error(t('onboarding_error_workspace_required'));
      if(!ONBOARDING.form.model) throw new Error(t('onboarding_error_model_required'));
    }
    if(ONBOARDING.steps[ONBOARDING.step]==='password'){
      ONBOARDING.form.password=(($('onboardingPasswordInput')||{}).value||'').trim();
    }
    if(ONBOARDING.step===ONBOARDING.steps.length-1){
      await _finishOnboarding();
      return;
    }
    ONBOARDING.step++;
    _renderOnboardingSteps();
    _renderOnboardingBody();
  }catch(e){
    _setOnboardingNotice(e.message||String(e),'warn');
  }
}
