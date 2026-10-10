// Super Video - Client Application Logic

// Blindage 1 : Protection Anti-Inspecteur & Anti-Copie Desktop
document.addEventListener("contextmenu", (e) => {
  const tag = e.target && e.target.tagName ? e.target.tagName.toUpperCase() : "";
  if (tag !== "INPUT" && tag !== "TEXTAREA") {
    e.preventDefault();
  }
});

document.addEventListener("keydown", (e) => {
  const key = (e.key || "").toUpperCase();
  const ctrlOrCmd = e.ctrlKey || e.metaKey;
  const shiftOrAlt = e.shiftKey || e.altKey;
  if (
    e.key === "F12" ||
    (ctrlOrCmd && shiftOrAlt && ["I", "J", "C", "K"].includes(key)) ||
    (ctrlOrCmd && key === "U")
  ) {
    e.preventDefault();
    e.stopPropagation();
    return false;
  }
});

document.addEventListener("DOMContentLoaded", () => {
  // Éléments du DOM
  const fileInput = document.getElementById("fileInput");
  const dropZone = document.getElementById("dropZone");
  const uploadEmptyState = document.getElementById("uploadEmptyState");
  const uploadPreviewState = document.getElementById("uploadPreviewState");
  const uploadLoadingState = document.getElementById("uploadLoadingState");
  const uploadBadge = document.getElementById("uploadBadge");
  const imagePreview = document.getElementById("imagePreview");
  const imageFilename = document.getElementById("imageFilename");
  const imageFileSize = document.getElementById("imageFileSize");
  const btnRemoveImage = document.getElementById("btnRemoveImage");

  const promptInput = document.getElementById("promptInput");
  const durationSlider = document.getElementById("durationSlider");
  const durationValue = document.getElementById("durationValue");
  const ratioButtons = document.querySelectorAll(".ratio-btn");
  const modelSelect = document.getElementById("modelSelect");
  const sizeSelect = document.getElementById("sizeSelect");
  const btnGenerate = document.getElementById("btnGenerate");
  const generateBtnText = document.getElementById("generateBtnText");

  const playerContainer = document.getElementById("playerContainer");
  const videoPlayer = document.getElementById("videoPlayer");
  const playerPlaceholder = document.getElementById("playerPlaceholder");
  const processingOverlay = document.getElementById("processingOverlay");
  const progressPercentageText = document.getElementById("progressPercentageText");
  const progressBarFill = document.getElementById("progressBarFill");
  const processStatus = document.getElementById("processStatus");
  const playerBadge = document.getElementById("playerBadge");
  const btnDownload = document.getElementById("btnDownload");
  const fileInfoBox = document.getElementById("fileInfoBox");
  const savedPathLabel = document.getElementById("savedPathLabel");
  const historyGrid = document.getElementById("historyGrid");
  const btnRefreshHistory = document.getElementById("btnRefreshHistory");

  // Modal Paramètres
  const btnOpenSettings = document.getElementById("btnOpenSettings");
  const settingsModal = document.getElementById("settingsModal");
  const btnCloseSettings = document.getElementById("btnCloseSettings");
  const btnCancelSettings = document.getElementById("btnCancelSettings");
  const btnSaveApiKey = document.getElementById("btnSaveApiKey");
  const inputApiKey = document.getElementById("inputApiKey");
  const apiKeyDot = document.getElementById("apiKeyDot");
    const apiKeyText = document.getElementById("apiKeyText");
  const apiKeyAlert = document.getElementById("apiKeyAlert");
  const selectProvider = document.getElementById("selectProvider");
  const customUrlContainer = document.getElementById("customUrlContainer");
  const inputBaseUrl = document.getElementById("inputBaseUrl");
  const inputCustomModel = document.getElementById("inputCustomModel");
  const providerHelpHint = document.getElementById("providerHelpHint");
  const btnResetFreePool = document.getElementById("btnResetFreePool");
  const ratioDetectedInfo = document.getElementById("ratioDetectedInfo");
  const ratioDetectedText = document.getElementById("ratioDetectedText");

  // Modal Mises à jour
  const btnOpenUpdates = document.getElementById("btnOpenUpdates");
  const updateNotificationDot = document.getElementById("updateNotificationDot");
  const updateModal = document.getElementById("updateModal");
  const btnCloseUpdateModal = document.getElementById("btnCloseUpdateModal");
  const btnCancelUpdate = document.getElementById("btnCancelUpdate");
  const btnRecheckUpdate = document.getElementById("btnRecheckUpdate");
  const btnApplyUpdate = document.getElementById("btnApplyUpdate");
  const updateCheckLoading = document.getElementById("updateCheckLoading");
  const updateContent = document.getElementById("updateContent");
  const updateStatusBanner = document.getElementById("updateStatusBanner");
  const updateStatusIcon = document.getElementById("updateStatusIcon");
  const updateStatusTitle = document.getElementById("updateStatusTitle");
  const updateStatusDesc = document.getElementById("updateStatusDesc");
  const currentVersionTag = document.getElementById("currentVersionTag");
  const latestVersionTag = document.getElementById("latestVersionTag");
  const updateMessageContainer = document.getElementById("updateMessageContainer");
  const updateCommitMsg = document.getElementById("updateCommitMsg");
  const updateProgressBox = document.getElementById("updateProgressBox");
  const updateProgressLabel = document.getElementById("updateProgressLabel");

  // Mode Studio & Contrôles Motion Design
  const tabModeMotion = document.getElementById("tabModeMotion");
  const tabModeCinema = document.getElementById("tabModeCinema");
  const panelMotionDesign = document.getElementById("panelMotionDesign");
  const panelCinemaMode = document.getElementById("panelCinemaMode");
  const cinemaPromptInput = document.getElementById("cinemaPromptInput");
  const motionDetailInput = document.getElementById("motionDetailInput");
  const cameraButtons = document.querySelectorAll(".camera-btn");

  // Storyboard & Rédacteur IA Elements
  const storyboardContainer = document.getElementById("storyboardContainer");
  const scenesTabList = document.getElementById("scenesTabList");
  const totalDurationBadge = document.getElementById("totalDurationBadge");
  const totalDurationText = document.getElementById("totalDurationText");
  const btnEnhanceMotionPrompt = document.getElementById("btnEnhanceMotionPrompt");
  const btnEnhanceMotionLabel = document.getElementById("btnEnhanceMotionLabel");
  const btnEnhanceCinemaPrompt = document.getElementById("btnEnhanceCinemaPrompt");
  const btnEnhanceCinemaLabel = document.getElementById("btnEnhanceCinemaLabel");
  const btnGenerateAllScenes = document.getElementById("btnGenerateAllScenes");
  const generateAllBtnText = document.getElementById("generateAllBtnText");
  const scenePlayerBar = document.getElementById("scenePlayerBar");
  const scenePlayerStatus = document.getElementById("scenePlayerStatus");
  const scenePlayerChips = document.getElementById("scenePlayerChips");

  // État local
  let currentStudioMode = "motion"; // "motion" ou "cinema"
  let currentCamera = "push_in";
  let currentImageUrl = null;
  let currentLocalImagePath = null;
  let currentRatio = "original";
  let detectedImagePreset = null;
  let activeEventSource = null;

  // État Multi-Scènes / Storyboard
  let scenes = [
    {
      id: 1,
      title: "Scène 1",
      duration: 5,
      camera: "push_in",
      char_lock: "statue_25d",
      fx: { fxShine: false, fxLights: false, fxSmoke: false, fxWind: false, fxConfetti: false, fxSparks: false },
      motionDetail: "",
      cinemaPrompt: "",
      status: "idle",
      videoUrl: null,
      filename: null
    }
  ];
  let activeSceneIndex = 0;
  let isGeneratingAllScenes = false;

  // Éléments de l'écran de démarrage (Splash Screen signé)
  const startupSplash = document.getElementById("startupSplash");
  const splashProgressBar = document.getElementById("splashProgressBar");
  const splashStatusText = document.getElementById("splashStatusText");
  const btnSkipSplash = document.getElementById("btnSkipSplash");
  const btnCreatorBadge = document.getElementById("btnCreatorBadge");

  function hideStartupSplash() {
    if (!startupSplash) return;
    startupSplash.classList.add("opacity-0", "pointer-events-none");
    setTimeout(() => {
      startupSplash.classList.add("hidden");
    }, 700);
  }

  function showStartupSplash() {
    if (!startupSplash) return;
    startupSplash.classList.remove("hidden");
    requestAnimationFrame(() => {
      startupSplash.classList.remove("opacity-0", "pointer-events-none");
    });
    if (splashProgressBar) splashProgressBar.style.width = "100%";
    if (splashStatusText) splashStatusText.textContent = "Studio Motion & Vidéo IA actif ✓";
  }

  if (startupSplash) {
    setTimeout(() => {
      if (splashProgressBar) splashProgressBar.style.width = "60%";
      if (splashStatusText) splashStatusText.textContent = "Chargement du Studio Motion Design & Vidéo...";
    }, 700);

    setTimeout(() => {
      if (splashProgressBar) splashProgressBar.style.width = "100%";
      if (splashStatusText) splashStatusText.textContent = "Prêt ! Bienvenue dans Super Video AI.";
    }, 1800);

    setTimeout(() => {
      hideStartupSplash();
    }, 3000);
  }

  if (btnSkipSplash) {
    btnSkipSplash.addEventListener("click", hideStartupSplash);
  }

  if (btnCreatorBadge) {
    btnCreatorBadge.addEventListener("click", showStartupSplash);
  }

  // 1. Initialisation : vérifier la clé API et charger l'historique
  checkApiKeyStatus();
  loadHistory();

  const PROVIDER_INFO = {
    default: {
      url: "",
      model: "",
      hint: "⚡ Mode Gratuit Inclus : utilise le Pool de 5 clés en rotation automatique (5 vidéos/jour). Vous pouvez aussi coller une clé Studio personnelle pour passer en illimité.",
      showCustom: false,
      models: [
        { value: "studio-v2.0", label: "Super Video Engine v2.0 (Standard HD - Inclus)" }
      ]
    },
    google_veo: {
      url: "https://generativelanguage.googleapis.com/v1beta",
      model: "veo-3.0-generate-preview",
      hint: "🎬 Google Veo Direct (sans aller sur Google Flow) : collez votre clé Google AI Studio (commençant par AIza...). Compatible Veo 3 et Veo 2 en Image-to-Video !",
      showCustom: true,
      models: [
        { value: "veo-3.0-generate-preview", label: "Google Veo 3.0 (Cinéma & Motion HD)" },
        { value: "veo-2.0-generate-001", label: "Google Veo 2.0 (Stable Image-to-Video)" }
      ]
    },
    openai_sora: {
      url: "https://api.openai.com/v1",
      model: "sora-2",
      hint: "🎥 OpenAI Sora : collez votre clé API OpenAI (sk-...) ou l'URL de votre passerelle compatible Sora.",
      showCustom: true,
      models: [
        { value: "sora-2", label: "OpenAI Sora 2 (Standard)" },
        { value: "sora-2-pro", label: "OpenAI Sora 2 Pro (Haute Fidélité)" }
      ]
    },
    kling_ai: {
      url: "https://api.klingai.com/v1",
      model: "kling-v2",
      hint: "🔥 Kling AI : collez votre clé Kling (ou l'URL de votre passerelle Kling v2 / v1.6).",
      showCustom: true,
      models: [
        { value: "kling-v2", label: "Kling 2.0 Master (Image-to-Video)" },
        { value: "kling-v1-6", label: "Kling 1.6 Pro (Motion Design)" }
      ]
    },
    higgsfield: {
      url: "https://api.higgsfield.ai/v1",
      model: "higgsfield-dop",
      hint: "✨ Higgsfield AI : collez votre clé API Higgsfield (DoP Cinema / Diffuse) et ajustez l'URL si vous passez par un hub.",
      showCustom: true,
      models: [
        { value: "higgsfield-dop", label: "Higgsfield DoP (Cinéma Caméra)" },
        { value: "higgsfield-diffuse", label: "Higgsfield Diffuse (Animation Personnage)" }
      ]
    },
    fal_ai: {
      url: "https://queue.fal.run",
      model: "fal-ai/kling-video/v2/master/image-to-video",
      hint: "🚀 Fal.ai Hub : collez votre clé Fal (key_id:key_secret) pour utiliser Veo 3, Kling 2.0, Runway Gen-3, Luma Ray 2 ou MiniMax Hailuo.",
      showCustom: true,
      models: [
        { value: "fal-ai/kling-video/v2/master/image-to-video", label: "Fal • Kling 2.0 Master" },
        { value: "fal-ai/veo3", label: "Fal • Google Veo 3" },
        { value: "fal-ai/runway-gen3/turbo/image-to-video", label: "Fal • Runway Gen-3 Turbo" },
        { value: "fal-ai/luma-dream-machine/ray-2/image-to-video", label: "Fal • Luma Ray 2" },
        { value: "fal-ai/minimax/video-01-live/image-to-video", label: "Fal • Hailuo MiniMax Live" }
      ]
    },
    custom: {
      url: "",
      model: "",
      hint: "🛠️ Serveur Personnalisé : indiquez l'URL de votre serveur (/v1), le nom du modèle (veo3, sora-2, kling-v2...) et votre clé d'activation.",
      showCustom: true,
      models: [
        { value: "studio-v2.0", label: "Modèle du Serveur Personnalisé (Actif)" }
      ]
    }
  };

  function updateProviderUI(mode, existingUrl = "", existingModel = "") {
    const info = PROVIDER_INFO[mode] || PROVIDER_INFO.custom;
    if (providerHelpHint) {
      providerHelpHint.textContent = info.hint;
      providerHelpHint.classList.remove("hidden");
    }
    if (info.showCustom) {
      customUrlContainer.classList.remove("hidden");
      inputBaseUrl.value = existingUrl || info.url;
      if (inputCustomModel) {
        inputCustomModel.value = existingModel || info.model;
      }
    } else {
      customUrlContainer.classList.add("hidden");
      inputBaseUrl.value = "";
      if (inputCustomModel) inputCustomModel.value = "";
    }
  }

  function syncStudioModelSelect(mode, customModel = "") {
    if (!modelSelect) return;
    const info = PROVIDER_INFO[mode] || PROVIDER_INFO.default;
    modelSelect.innerHTML = "";
    if (customModel && !info.models.some(m => m.value === customModel)) {
      const optCustom = document.createElement("option");
      optCustom.value = customModel;
      optCustom.textContent = `${customModel} (Modèle personnalisé actif)`;
      modelSelect.appendChild(optCustom);
    }
    info.models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.value;
      opt.textContent = m.label;
      if (customModel && m.value === customModel) opt.selected = true;
      modelSelect.appendChild(opt);
    });
  }

  // Gestion du changement de fournisseur
  if (selectProvider) {
    selectProvider.addEventListener("change", () => {
      updateProviderUI(selectProvider.value);
    });
  }

  // 2. Gestion de la clé API et du Pool Hybride (Solution C + Multi-Moteurs)
  async function checkApiKeyStatus() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      const poolTitle = document.getElementById("poolStatusTitle");
      const poolDesc = document.getElementById("poolStatusDesc");
      const mode = data.provider_mode || "default";

      if (btnResetFreePool) {
        if (!data.is_shared_pool || mode !== "default") {
          btnResetFreePool.classList.remove("hidden");
        } else {
          btnResetFreePool.classList.add("hidden");
        }
      }

      if (data.configured) {
        apiKeyDot.className = "w-2 h-2 rounded-full bg-emerald-400";
        if (data.is_shared_pool && mode === "default") {
          const remaining = Math.max(0, (data.quota_limit || 5) - (data.quota_used || 0));
          apiKeyText.textContent = `Studio Actif (${remaining}/${data.quota_limit || 5} aujourd'hui)`;
          if (poolTitle) poolTitle.textContent = `Pool Communautaire Actif (${remaining}/${data.quota_limit || 5} vidéos restantes aujourd'hui)`;
          if (poolDesc) poolDesc.textContent = `Rotation multi-clés automatique active (${data.pool_size || 5} clés dans le coffre-fort). Ou connectez votre propre serveur/clé (Veo 3, Sora 2, Kling, Higgsfield) ci-dessous !`;
        } else {
          const engineNames = {
            default: "Studio Pro",
            google_veo: "Google Veo",
            openai_sora: "OpenAI Sora",
            kling_ai: "Kling AI",
            higgsfield: "Higgsfield",
            fal_ai: "Fal.ai Hub",
            custom: "Serveur Custom"
          };
          const eLabel = engineNames[mode] || "Clé Pro";
          apiKeyText.textContent = `${eLabel} : ${data.masked_key} (Illimité)`;
          if (poolTitle) poolTitle.textContent = `Mode Personnel Illimité Actif (${eLabel}) ✓`;
          if (poolDesc) poolDesc.textContent = `Votre clé (${data.masked_key}) est connectée à ${eLabel} sans limite journalière.`;
        }
      } else {
        apiKeyDot.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
        apiKeyText.textContent = "Clé requise pour ce moteur";
      }

      selectProvider.value = PROVIDER_INFO[mode] ? mode : "custom";
      updateProviderUI(
        selectProvider.value,
        data.base_url === "default" ? "" : (data.base_url || ""),
        data.custom_model || ""
      );
      syncStudioModelSelect(selectProvider.value, data.custom_model || "");
    } catch (e) {
      console.error("Erreur statut clé:", e);
    }
  }

  btnOpenSettings.addEventListener("click", () => {
    settingsModal.classList.remove("hidden");
    apiKeyAlert.classList.add("hidden");
  });

  const closeSettings = () => settingsModal.classList.add("hidden");
  btnCloseSettings.addEventListener("click", closeSettings);
  btnCancelSettings.addEventListener("click", closeSettings);

  if (btnResetFreePool) {
    btnResetFreePool.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/settings/reset", { method: "POST" });
        if (res.ok) {
          showAlert(apiKeyAlert, "Retour au Pool Gratuit Super Video AI (5 vidéos/jour) activé !", "success");
          inputApiKey.value = "";
          await checkApiKeyStatus();
        }
      } catch (err) {
        showAlert(apiKeyAlert, "Erreur lors de la réinitialisation.", "error");
      }
    });
  }

  btnSaveApiKey.addEventListener("click", async () => {
    const key = inputApiKey.value.trim();
    const mode = selectProvider.value;
    const info = PROVIDER_INFO[mode] || PROVIDER_INFO.custom;
    const chosenUrl = info.showCustom ? (inputBaseUrl.value.trim() || info.url) : "default";
    const chosenModel = (info.showCustom && inputCustomModel) ? inputCustomModel.value.trim() : "";

    const payload = {
      provider_mode: mode,
      base_url: chosenUrl || "default",
      custom_model: chosenModel
    };
    if (key) payload.api_key = key;

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showAlert(apiKeyAlert, "Configuration enregistrée avec succès !", "success");
        await checkApiKeyStatus();
        inputApiKey.value = "";
        setTimeout(closeSettings, 1000);
      } else {
        showAlert(apiKeyAlert, data.detail || "Erreur lors de l'enregistrement.", "error");
      }
    } catch (err) {
      showAlert(apiKeyAlert, "Erreur réseau.", "error");
    }
  });

  function showAlert(elem, msg, type) {
    elem.classList.remove("hidden");
    if (type === "success") {
      elem.className = "p-3 rounded-xl text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    } else {
      elem.className = "p-3 rounded-xl text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20";
    }
    elem.textContent = msg;
  }

  // 3. Gestion Drag & Drop et Upload Visuel
  ["dragenter", "dragover"].forEach(event => {
    dropZone.addEventListener(event, (e) => {
      e.preventDefault();
      dropZone.classList.add("border-brand-purple", "bg-slate-900/80");
    });
  });

  ["dragleave", "drop"].forEach(event => {
    dropZone.addEventListener(event, (e) => {
      e.preventDefault();
      dropZone.classList.remove("border-brand-purple", "bg-slate-900/80");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  });

  async function handleFileUpload(file) {
    // Vérification de base côté client
    const allowed = ["image/png", "image/jpeg", "image/webp"];
    if (!allowed.includes(file.type)) {
      alert("Format de fichier non supporté. Veuillez choisir un fichier PNG, JPG ou WEBP.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      alert("L'image dépasse 15 Mo.");
      return;
    }

    uploadEmptyState.classList.add("hidden");
    uploadPreviewState.classList.add("hidden");
    uploadLoadingState.classList.remove("hidden");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      const result = await res.json();

      if (res.ok && result.success) {
        const d = result.data;
        currentImageUrl = d.public_url;
        currentLocalImagePath = d.local_path;

        detectedImagePreset = d;
        imagePreview.src = d.preview_url;
        
        // Sélection automatique du mode original / sans coupure
        const btnOriginal = document.querySelector('.ratio-btn[data-ratio="original"]');
        if (btnOriginal) {
          ratioButtons.forEach(b => {
            b.classList.remove("active", "border-brand-cyan/40", "bg-brand-cyan/10", "text-brand-cyan");
          });
          btnOriginal.classList.add("active", "border-brand-cyan/40", "bg-brand-cyan/10", "text-brand-cyan");
          currentRatio = "original";
        }

        if (ratioDetectedInfo && ratioDetectedText) {
          ratioDetectedInfo.classList.remove("hidden");
          ratioDetectedInfo.classList.add("flex");
          ratioDetectedText.textContent = `Image ${d.width}×${d.height} → Cadrage auto sélectionné : ${d.ratio_label} (sans coupure)`;
        }

        imageFilename.textContent = d.filename;
        imageFileSize.textContent = formatBytes(d.size_bytes);

        uploadLoadingState.classList.add("hidden");
        uploadPreviewState.classList.remove("hidden");
        uploadBadge.classList.remove("hidden");
      } else {
        throw new Error(result.detail || "Échec de l'upload.");
      }
    } catch (err) {
      alert("Erreur lors de la préparation de l'image : " + err.message);
      resetImageUpload();
    }
  }

  function resetImageUpload() {
    currentImageUrl = null;
    currentLocalImagePath = null;
    detectedImagePreset = null;
    fileInput.value = "";
    if (ratioDetectedInfo) {
      ratioDetectedInfo.classList.add("hidden");
      ratioDetectedInfo.classList.remove("flex");
    }
    uploadLoadingState.classList.add("hidden");
    uploadPreviewState.classList.add("hidden");
    uploadEmptyState.classList.remove("hidden");
    uploadBadge.classList.add("hidden");
  }

  btnRemoveImage.addEventListener("click", (e) => {
    e.stopPropagation();
    resetImageUpload();
  });

  function formatBytes(bytes) {
    if (!bytes) return "0 Ko";
    const k = 1024;
    const sizes = ["Octets", "Ko", "Mo"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // 4. Gestion des Modes : Motion Design vs Cinématique
  if (tabModeMotion && tabModeCinema) {
    tabModeMotion.addEventListener("click", () => {
      currentStudioMode = "motion";
      tabModeMotion.className = "mode-tab-btn active py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 bg-gradient-to-r from-brand-violet to-brand-purple text-white shadow-md shadow-brand-violet/25";
      tabModeCinema.className = "mode-tab-btn py-2.5 px-3 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 text-slate-400 hover:text-white hover:bg-slate-800/60";
      panelMotionDesign.classList.remove("hidden");
      panelCinemaMode.classList.add("hidden");
      generateBtnText.textContent = `Générer le Motion Design (${parseFloat(durationSlider.value).toFixed(1)}s)`;
    });

    tabModeCinema.addEventListener("click", () => {
      currentStudioMode = "cinema";
      tabModeCinema.className = "mode-tab-btn active py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 bg-gradient-to-r from-brand-cyan to-blue-600 text-white shadow-md shadow-brand-cyan/25";
      tabModeMotion.className = "mode-tab-btn py-2.5 px-3 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-1.5 text-slate-400 hover:text-white hover:bg-slate-800/60";
      panelCinemaMode.classList.remove("hidden");
      panelMotionDesign.classList.add("hidden");
      generateBtnText.textContent = `Générer la vidéo (${parseFloat(durationSlider.value).toFixed(1)}s)`;
    });
  }

  // 4b. Gestion des boutons Caméra
  cameraButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      cameraButtons.forEach(b => {
        b.className = "camera-btn p-2 rounded-xl border border-brand-border bg-slate-900/60 text-slate-300 text-xs font-semibold flex items-center justify-center gap-1 hover:bg-slate-800 transition-all";
      });
      btn.className = "camera-btn active p-2 rounded-xl border border-brand-purple bg-brand-purple/20 text-white text-xs font-semibold flex items-center justify-center gap-1 transition-all";
      currentCamera = btn.getAttribute("data-camera");
    });
  });

  // 4c. Interaction visuelle sur les puces FX
  document.querySelectorAll(".fx-chip-label").forEach(chip => {
    const cb = chip.querySelector('input[type="checkbox"]');
    if (cb) {
      cb.addEventListener("change", () => {
        if (cb.checked) {
          chip.className = "fx-chip-label cursor-pointer select-none p-2 rounded-xl border border-brand-cyan/40 bg-brand-cyan/10 hover:bg-brand-cyan/20 transition-all flex items-center gap-2";
          const sp = chip.querySelector("span");
          if (sp) sp.className = "text-xs text-white font-medium";
        } else {
          chip.className = "fx-chip-label cursor-pointer select-none p-2 rounded-xl border border-brand-border bg-slate-900/50 hover:bg-slate-800 transition-all flex items-center gap-2";
          const sp = chip.querySelector("span");
          if (sp) sp.className = "text-xs text-slate-400 font-medium";
        }
      });
    }
  });

  // 4d. Interaction sur les radios Character Lock
  document.querySelectorAll('input[name="char_lock"]').forEach(radio => {
    radio.addEventListener("change", () => {
      document.querySelectorAll(".motion-radio-label").forEach(label => {
        const r = label.querySelector('input[name="char_lock"]');
        if (r && r.checked) {
          label.className = "motion-radio-label cursor-pointer p-2.5 rounded-xl border border-brand-purple/70 bg-brand-purple/20 transition-all flex flex-col gap-1";
          const sp = label.querySelector("span");
          const p = label.querySelector("p");
          if (sp) sp.className = "text-xs font-bold text-white flex items-center gap-1";
          if (p) p.className = "text-[10px] text-slate-300 leading-tight";
        } else {
          label.className = "motion-radio-label cursor-pointer p-2.5 rounded-xl border border-brand-border bg-slate-900/60 hover:border-brand-purple/50 transition-all flex flex-col gap-1";
          const sp = label.querySelector("span");
          const p = label.querySelector("p");
          if (sp) sp.className = "text-xs font-semibold text-slate-300 flex items-center gap-1";
          if (p) p.className = "text-[10px] text-slate-400 leading-tight";
        }
      });
    });
  });

  // 4e. Presets Cinéma
  document.querySelectorAll("[data-cinema]").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = btn.getAttribute("data-cinema");
      if (cinemaPromptInput) {
        if (cinemaPromptInput.value.trim()) {
          cinemaPromptInput.value = cinemaPromptInput.value.trim() + ", " + p;
        } else {
          cinemaPromptInput.value = p;
        }
      }
    });
  });

  // Compilateur intelligent de prompt Motion Design
  function compileMotionDesignPrompt() {
    const charLockEl = document.querySelector('input[name="char_lock"]:checked');
    const charLockVal = charLockEl ? charLockEl.value : "statue_25d";

    let charPrompt = "";
    if (charLockVal === "statue_25d") {
      charPrompt = "The characters remain completely frozen in their exact poses like a high-end 2.5D broadcast motion graphic. Zero limb displacement, exact closed mouths, exact facial bone structure.";
    } else if (charLockVal === "micro_breathing") {
      charPrompt = "The characters remain strictly in their exact poses with subtle natural chest breathing and living micro-movements on place. Facial features and closed eyes 100% frozen.";
    } else {
      charPrompt = "The characters maintain their exact poses with delicate eye blinks and subtle head drift. Strict facial consistency.";
    }

    const fxList = [];
    if (document.getElementById("fxShine")?.checked) {
      fxList.push("specular golden shimmer, glints, and light sweeps sparkling across the trophy and metallic surfaces");
    }
    if (document.getElementById("fxConfetti")?.checked) {
      fxList.push("celebratory golden confetti and stadium victory particles drifting dynamically across the air");
    }
    if (document.getElementById("fxLights")?.checked) {
      fxList.push("volumetric atmospheric stadium floodlights and dynamic lighting beams crossing in the background");
    }
    if (document.getElementById("fxSmoke")?.checked) {
      fxList.push("subtle cinematic atmospheric fog and haze drifting gently behind the subjects");
    }
    if (document.getElementById("fxWind")?.checked) {
      fxList.push("gentle natural breeze fluttering the fabric edges and jerseys");
    }
    if (document.getElementById("fxSparks")?.checked) {
      fxList.push("energetic floating luminous sparks and light embers in the air");
    }

    let cameraPrompt = "Slow cinematic push-in dolly camera movement creating subtle depth.";
    if (currentCamera === "parallax_drift") {
      cameraPrompt = "Subtle 3D parallax floating camera drift highlighting background layers.";
    } else if (currentCamera === "pan_horizontal") {
      cameraPrompt = "Slow smooth horizontal cinematic tracking pan.";
    } else if (currentCamera === "static") {
      cameraPrompt = "Static locked-off camera with dynamic living atmosphere and lighting.";
    }

    const detail = motionDetailInput ? motionDetailInput.value.trim() : "";

    let finalCompiled = `Cinematic 2.5D motion design animation of the exact original visuel. ${charPrompt} `;
    if (fxList.length > 0) {
      finalCompiled += `Dynamic environmental motion: ${fxList.join(", ")}. `;
    }
    finalCompiled += `${cameraPrompt} Broadcast motion poster quality. `;
    if (detail) {
      finalCompiled += `Additional styling: ${detail}.`;
    }
    return finalCompiled;
  }

  // ==========================================
  // SYSTÈME DE STORYBOARD & MULTI-SCÈNES
  // ==========================================

  function saveCurrentSceneInputs() {
    if (!scenes[activeSceneIndex]) return;
    const s = scenes[activeSceneIndex];
    s.duration = parseFloat(durationSlider.value) || 5;
    s.camera = currentCamera;

    const charLockEl = document.querySelector('input[name="char_lock"]:checked');
    if (charLockEl) s.char_lock = charLockEl.value;

    s.fx = {
      fxShine: document.getElementById("fxShine")?.checked || false,
      fxLights: document.getElementById("fxLights")?.checked || false,
      fxSmoke: document.getElementById("fxSmoke")?.checked || false,
      fxWind: document.getElementById("fxWind")?.checked || false,
      fxConfetti: document.getElementById("fxConfetti")?.checked || false,
      fxSparks: document.getElementById("fxSparks")?.checked || false,
    };

    if (motionDetailInput) s.motionDetail = motionDetailInput.value;
    if (cinemaPromptInput) s.cinemaPrompt = cinemaPromptInput.value;
  }

  function loadSceneInputs(index) {
    const s = scenes[index];
    if (!s) return;

    durationSlider.value = s.duration;
    durationValue.textContent = `${parseFloat(s.duration).toFixed(1)}s`;

    // Caméra
    currentCamera = s.camera || "push_in";
    cameraButtons.forEach(btn => {
      if (btn.getAttribute("data-camera") === currentCamera) {
        btn.className = "camera-btn active p-2 rounded-xl border border-brand-purple bg-brand-purple/20 text-white text-xs font-semibold flex items-center justify-center gap-1 transition-all";
      } else {
        btn.className = "camera-btn p-2 rounded-xl border border-brand-border bg-slate-900/60 text-slate-300 text-xs font-semibold flex items-center justify-center gap-1 hover:bg-slate-800 transition-all";
      }
    });

    // Character Lock
    const charLockRadio = document.querySelector(`input[name="char_lock"][value="${s.char_lock || 'statue_25d'}"]`);
    if (charLockRadio) {
      charLockRadio.checked = true;
      charLockRadio.dispatchEvent(new Event("change"));
    }

    // Effets FX
    if (s.fx) {
      Object.keys(s.fx).forEach(fxId => {
        const el = document.getElementById(fxId);
        if (el) {
          el.checked = !!s.fx[fxId];
          el.dispatchEvent(new Event("change"));
        }
      });
    }

    // Détail libre & Prompt cinéma
    if (motionDetailInput) motionDetailInput.value = s.motionDetail || "";
    if (cinemaPromptInput) cinemaPromptInput.value = s.cinemaPrompt || "";

    updateGenerateButtonLabels();
  }

  function updateTotalDurationBadge() {
    const totalSecs = scenes.reduce((acc, sc) => acc + (parseFloat(sc.duration) || 5), 0);
    if (totalDurationText) {
      totalDurationText.textContent = `${totalSecs.toFixed(1)}s (${scenes.length} scène${scenes.length > 1 ? 's' : ''})`;
    }
    if (btnGenerateAllScenes) {
      if (scenes.length > 1) {
        btnGenerateAllScenes.classList.remove("hidden");
        if (generateAllBtnText) {
          generateAllBtnText.textContent = `Générer tout le Storyboard (${totalSecs.toFixed(1)}s • ${scenes.length} scènes)`;
        }
      } else {
        btnGenerateAllScenes.classList.add("hidden");
      }
    }
  }

  function updateGenerateButtonLabels() {
    const curSec = parseFloat(durationSlider.value).toFixed(1);
    const sceneNum = scenes[activeSceneIndex] ? scenes[activeSceneIndex].id : 1;
    if (scenes.length > 1) {
      generateBtnText.textContent = currentStudioMode === "motion"
        ? `Générer la Scène ${sceneNum} (${curSec}s)`
        : `Générer la Scène ${sceneNum} (${curSec}s)`;
    } else {
      generateBtnText.textContent = currentStudioMode === "motion"
        ? `Générer le Motion Design (${curSec}s)`
        : `Générer la vidéo (${curSec}s)`;
    }
    updateTotalDurationBadge();
  }

  function renderScenesTabs() {
    if (!scenesTabList) return;
    scenesTabList.innerHTML = "";

    scenes.forEach((s, idx) => {
      const isActive = idx === activeSceneIndex;
      const tab = document.createElement("div");
      tab.className = `group flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer transition-all border shrink-0 select-none ${
        isActive
          ? "bg-brand-purple/20 text-white border-brand-purple shadow-md shadow-brand-purple/20 font-bold"
          : "bg-slate-900/60 text-slate-300 border-brand-border/70 hover:bg-slate-800 hover:text-white"
      }`;

      let icon = "🎬";
      if (s.status === "ready") icon = "✅";
      else if (s.status === "generating") icon = "⏳";

      tab.innerHTML = `
        <span class="text-xs">${icon}</span>
        <span>Scène ${s.id}</span>
        <span class="text-[10px] px-1.5 py-0.2 rounded-md ${
          isActive ? "bg-brand-purple/40 text-brand-cyan" : "bg-slate-800 text-slate-400"
        }">${parseFloat(s.duration).toFixed(0)}s</span>
      `;

      if (scenes.length > 1) {
        const btnDel = document.createElement("button");
        btnDel.type = "button";
        btnDel.className = "ml-1 text-slate-400 hover:text-rose-400 p-0.5 rounded transition-colors text-xs leading-none";
        btnDel.innerHTML = "×";
        btnDel.title = `Supprimer la Scène ${s.id}`;
        btnDel.addEventListener("click", (e) => {
          e.stopPropagation();
          deleteScene(idx);
        });
        tab.appendChild(btnDel);
      }

      tab.addEventListener("click", () => {
        if (activeSceneIndex !== idx) {
          switchActiveScene(idx);
        }
      });

      scenesTabList.appendChild(tab);
    });

    if (scenes.length < 8) {
      const btnAdd = document.createElement("button");
      btnAdd.type = "button";
      btnAdd.className = "flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold text-brand-cyan bg-slate-900/40 hover:bg-brand-cyan/10 border border-dashed border-brand-cyan/40 hover:border-brand-cyan transition-all shrink-0 active:scale-95";
      btnAdd.innerHTML = `
        <span class="text-xs">+</span>
        <span>Ajouter une scène</span>
      `;
      btnAdd.addEventListener("click", addScene);
      scenesTabList.appendChild(btnAdd);
    }

    updateTotalDurationBadge();
  }

  function switchActiveScene(newIndex) {
    saveCurrentSceneInputs();
    activeSceneIndex = newIndex;
    loadSceneInputs(newIndex);
    renderScenesTabs();
  }

  function addScene() {
    saveCurrentSceneInputs();
    const newId = scenes.length + 1;
    const prevScene = scenes[scenes.length - 1];
    scenes.push({
      id: newId,
      title: `Scène ${newId}`,
      duration: prevScene ? prevScene.duration : 5,
      camera: "push_in",
      char_lock: prevScene ? prevScene.char_lock : "statue_25d",
      fx: prevScene ? { ...prevScene.fx } : { fxShine: true },
      motionDetail: "",
      cinemaPrompt: "",
      status: "idle",
      videoUrl: null,
      filename: null
    });
    activeSceneIndex = scenes.length - 1;
    loadSceneInputs(activeSceneIndex);
    renderScenesTabs();
  }

  function deleteScene(index) {
    if (scenes.length <= 1) return;
    saveCurrentSceneInputs();
    scenes.splice(index, 1);
    scenes.forEach((s, i) => {
      s.id = i + 1;
      s.title = `Scène ${i + 1}`;
    });
    if (activeSceneIndex >= scenes.length) {
      activeSceneIndex = scenes.length - 1;
    }
    loadSceneInputs(activeSceneIndex);
    renderScenesTabs();
    renderScenePlayerBar();
  }

  function renderScenePlayerBar() {
    if (!scenePlayerBar || !scenePlayerChips) return;
    const readyScenes = scenes.filter(s => s.videoUrl);
    if (readyScenes.length === 0) {
      scenePlayerBar.classList.add("hidden");
      return;
    }

    scenePlayerBar.classList.remove("hidden");
    scenePlayerChips.innerHTML = "";

    scenes.forEach((s, idx) => {
      const chip = document.createElement("button");
      chip.type = "button";
      const isReady = !!s.videoUrl;
      chip.className = `px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border ${
        isReady
          ? (idx === activeSceneIndex
              ? "bg-brand-cyan/20 text-brand-cyan border-brand-cyan shadow-sm"
              : "bg-slate-800 text-slate-200 border-brand-border hover:bg-slate-700")
          : "bg-slate-900/50 text-slate-500 border-brand-border/40 cursor-not-allowed opacity-60"
      }`;

      chip.innerHTML = `
        <span>${isReady ? "▶" : "⏳"}</span>
        <span>Scène ${s.id}</span>
        <span class="text-[10px] text-slate-400">(${parseFloat(s.duration).toFixed(0)}s)</span>
      `;

      if (isReady) {
        chip.addEventListener("click", () => {
          activeSceneIndex = idx;
          loadSceneInputs(idx);
          renderScenesTabs();
          showCompletedVideo(s.videoUrl, s.filename);
          if (scenePlayerStatus) {
            scenePlayerStatus.textContent = `Lecture : Scène ${s.id}`;
          }
        });
      }

      scenePlayerChips.appendChild(chip);
    });
  }

  // ==========================================
  // RÉDACTEUR IA SUPER VIDEO (MAGIC PROMPT)
  // ==========================================

  async function triggerPromptEnhancement(isCinema = true) {
    saveCurrentSceneInputs();
    const targetInput = isCinema ? cinemaPromptInput : motionDetailInput;
    const targetLabel = isCinema ? btnEnhanceCinemaLabel : btnEnhanceMotionLabel;
    const targetBtn = isCinema ? btnEnhanceCinemaPrompt : btnEnhanceMotionPrompt;

    if (!targetInput || !targetBtn) return;

    const originalText = targetInput.value.trim();
    const originalLabel = targetLabel ? targetLabel.textContent : "Rédacteur IA SuperVideo";

    targetBtn.disabled = true;
    if (targetLabel) targetLabel.textContent = "Rédaction magique...";
    targetBtn.classList.add("opacity-80");

    try {
      const res = await fetch("/api/prompt/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: originalText,
          mode: currentStudioMode,
          scene_number: scenes[activeSceneIndex].id
        })
      });

      const data = await res.json();
      if (res.ok && data.success && data.enhanced_prompt) {
        targetInput.value = data.enhanced_prompt;
        saveCurrentSceneInputs();

        // Animation de mise en valeur visuelle
        targetInput.classList.add("ring-2", "ring-brand-cyan", "bg-slate-900/90");
        setTimeout(() => {
          targetInput.classList.remove("ring-2", "ring-brand-cyan");
        }, 1500);
      } else {
        alert("Le rédacteur IA n'a pas pu parfaire le prompt : " + (data.detail || "erreur"));
      }
    } catch (err) {
      console.error("Erreur enhance prompt:", err);
      alert("Erreur de connexion avec le rédacteur IA.");
    } finally {
      targetBtn.disabled = false;
      if (targetLabel) targetLabel.textContent = originalLabel;
      targetBtn.classList.remove("opacity-80");
    }
  }

  if (btnEnhanceCinemaPrompt) {
    btnEnhanceCinemaPrompt.addEventListener("click", () => triggerPromptEnhancement(true));
  }
  if (btnEnhanceMotionPrompt) {
    btnEnhanceMotionPrompt.addEventListener("click", () => triggerPromptEnhancement(false));
  }

  // 5. Durée Slider & Synchronisation
  durationSlider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value).toFixed(1);
    durationValue.textContent = `${val}s`;
    if (scenes[activeSceneIndex]) {
      scenes[activeSceneIndex].duration = parseFloat(val);
    }
    updateGenerateButtonLabels();
    renderScenesTabs();
  });

  if (motionDetailInput) {
    motionDetailInput.addEventListener("input", () => {
      if (scenes[activeSceneIndex]) {
        scenes[activeSceneIndex].motionDetail = motionDetailInput.value;
      }
    });
  }

  if (cinemaPromptInput) {
    cinemaPromptInput.addEventListener("input", () => {
      if (scenes[activeSceneIndex]) {
        scenes[activeSceneIndex].cinemaPrompt = cinemaPromptInput.value;
      }
    });
  }

  // 6. Cadrage Ratio
  ratioButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      ratioButtons.forEach(b => {
        b.classList.remove("active", "border-brand-cyan/40", "bg-brand-cyan/10", "text-brand-cyan");
      });
      btn.classList.add("active");
      currentRatio = btn.getAttribute("data-ratio");
      if (currentRatio === "original") {
        btn.classList.add("border-brand-cyan/40", "bg-brand-cyan/10", "text-brand-cyan");
      }
    });
  });

  // ==========================================
  // MOTEUR D'EXÉCUTION DE RENDU VIDÉO
  // ==========================================

  function calculateTargetDimensions() {
    let targetWidth = null;
    let targetHeight = null;

    if (currentRatio === "original" && detectedImagePreset) {
      targetWidth = detectedImagePreset.recommended_width;
      targetHeight = detectedImagePreset.recommended_height;
    } else if (currentRatio === "1:1") {
      targetWidth = 960;
      targetHeight = 960;
    } else if (currentRatio === "3:4") {
      targetWidth = 832;
      targetHeight = 1088;
    } else if (currentRatio === "4:3") {
      targetWidth = 1088;
      targetHeight = 832;
    } else if (currentRatio === "9:16") {
      targetWidth = 704;
      targetHeight = 1280;
    } else if (currentRatio === "16:9") {
      targetWidth = 1280;
      targetHeight = 704;
    }
    return { targetWidth, targetHeight };
  }

  function generateScenePromise(sceneIdx, sceneNum, totalScenesCount = 1) {
    return new Promise(async (resolve, reject) => {
      saveCurrentSceneInputs();
      const sc = scenes[sceneIdx];
      if (!sc) return reject(new Error("Scène introuvable"));

      let prompt = "";
      const isMotionDesign = currentStudioMode === "motion";

      if (isMotionDesign) {
        prompt = compileMotionDesignPrompt();
      } else {
        prompt = (sc.cinemaPrompt || (cinemaPromptInput ? cinemaPromptInput.value.trim() : "")).trim();
        if (!prompt) {
          return reject(new Error(`Veuillez renseigner un prompt pour la Scène ${sceneNum}.`));
        }
      }

      sc.status = "generating";
      renderScenesTabs();

      const { targetWidth, targetHeight } = calculateTargetDimensions();

      const payload = {
        prompt: prompt,
        image_url: currentImageUrl,
        model: modelSelect.value,
        mode: "keyframe",
        seconds: String(sc.duration),
        size: sizeSelect.value,
        aspect_ratio: currentRatio,
        target_width: targetWidth,
        target_height: targetHeight,
        motion_design_mode: isMotionDesign
      };

      try {
        const res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
          if (res.status === 401) {
            settingsModal.classList.remove("hidden");
            showAlert(apiKeyAlert, "Veuillez renseigner votre clé d'accès Studio pour continuer.", "error");
          }
          throw new Error(data.detail || "Échec de création de la tâche vidéo.");
        }

        const videoId = data.data.video_id || data.data.task_id || data.data.id;
        checkApiKeyStatus();

        if (activeEventSource) {
          activeEventSource.close();
        }

        const scenePrefix = totalScenesCount > 1 ? `[Scène ${sceneNum}/${totalScenesCount}] ` : "";
        updateProgress(15, `${scenePrefix}Tâche transmise au moteur Super Video AI...`);

        activeEventSource = new EventSource(`/api/stream/${videoId}?model=${encodeURIComponent(modelSelect.value)}`);

        activeEventSource.onmessage = (event) => {
          try {
            const info = JSON.parse(event.data);

            if (info.status === "completed") {
              updateProgress(100, `${scenePrefix}Téléchargement local terminé !`);
              activeEventSource.close();
              sc.status = "ready";
              sc.videoUrl = info.local_url;
              sc.filename = info.filename;
              renderScenesTabs();
              renderScenePlayerBar();
              resolve(info);
            } else if (info.status === "failed") {
              activeEventSource.close();
              sc.status = "error";
              renderScenesTabs();
              reject(new Error(info.error || "Rendu échoué"));
            } else if (info.status === "in_progress") {
              const prog = Math.max(20, info.progress || 35);
              updateProgress(prog, `${scenePrefix}${info.queue_message || `Calcul et rendu vidéo en cours (${prog}%)...`}`);
            } else if (info.status === "queued") {
              const qProg = Math.max(10, info.progress || 12);
              updateProgress(qProg, `${scenePrefix}${info.queue_message || "En file d'attente de rendu..."}`);
            }
          } catch (e) {
            console.error("Erreur parsing SSE:", e);
          }
        };

        activeEventSource.onerror = () => {
          console.warn("Connexion flux interrompue.");
        };

      } catch (err) {
        sc.status = "error";
        renderScenesTabs();
        reject(err);
      }
    });
  }

  // 7. Génération de la Scène Active
  btnGenerate.addEventListener("click", async () => {
    if (!currentImageUrl) {
      alert("Veuillez charger une image source à animer.");
      return;
    }

    btnGenerate.disabled = true;
    if (btnGenerateAllScenes) btnGenerateAllScenes.disabled = true;

    generateBtnText.textContent = "Lancement de la tâche...";
    playerBadge.textContent = "Génération...";
    playerBadge.className = "text-xs px-2 py-0.5 rounded-full bg-brand-violet/20 text-brand-purple font-medium";

    playerPlaceholder.classList.add("hidden");
    videoPlayer.classList.add("hidden");
    btnDownload.classList.add("hidden");
    fileInfoBox.classList.add("hidden");
    processingOverlay.classList.remove("hidden");
    updateProgress(5, "Initialisation du moteur Super Video AI...");

    try {
      const curScene = scenes[activeSceneIndex];
      const result = await generateScenePromise(activeSceneIndex, curScene.id, 1);
      showCompletedVideo(result.local_url, result.filename);
      loadHistory();
      finishProcessing(true);
    } catch (err) {
      alert("Erreur de génération : " + err.message);
      finishProcessing(false);
    } finally {
      if (btnGenerateAllScenes) btnGenerateAllScenes.disabled = false;
    }
  });

  // 7b. Génération séquentielle de tout le Storyboard
  if (btnGenerateAllScenes) {
    btnGenerateAllScenes.addEventListener("click", async () => {
      if (!currentImageUrl) {
        alert("Veuillez charger une image source à animer.");
        return;
      }

      btnGenerate.disabled = true;
      btnGenerateAllScenes.disabled = true;
      isGeneratingAllScenes = true;

      playerBadge.textContent = "Storyboard...";
      playerBadge.className = "text-xs px-2 py-0.5 rounded-full bg-brand-cyan/20 text-brand-cyan font-medium";

      playerPlaceholder.classList.add("hidden");
      videoPlayer.classList.add("hidden");
      btnDownload.classList.add("hidden");
      fileInfoBox.classList.add("hidden");
      processingOverlay.classList.remove("hidden");

      let firstVideoUrl = null;
      let firstFilename = null;

      try {
        for (let i = 0; i < scenes.length; i++) {
          activeSceneIndex = i;
          loadSceneInputs(i);
          renderScenesTabs();

          updateProgress(5, `Initialisation de la Scène ${scenes[i].id} sur ${scenes.length}...`);
          const res = await generateScenePromise(i, scenes[i].id, scenes.length);

          if (!firstVideoUrl) {
            firstVideoUrl = res.local_url;
            firstFilename = res.filename;
          }
        }

        if (firstVideoUrl) {
          activeSceneIndex = 0;
          loadSceneInputs(0);
          showCompletedVideo(firstVideoUrl, firstFilename);
        }
        loadHistory();
        finishProcessing(true);
        alert(`Félicitations ! Toutes les ${scenes.length} scènes de votre Storyboard ont été générées avec succès !`);
      } catch (err) {
        alert("Erreur lors de la génération du Storyboard : " + err.message);
        finishProcessing(false);
      } finally {
        isGeneratingAllScenes = false;
        btnGenerate.disabled = false;
        btnGenerateAllScenes.disabled = false;
      }
    });
  }


  function updateProgress(percent, statusMsg) {
    progressPercentageText.textContent = `${percent}%`;
    progressBarFill.style.width = `${percent}%`;
    processStatus.textContent = statusMsg;
  }

  let currentVideoFilename = null;
  const btnRevealFolder = document.getElementById("btnRevealFolder");

  function showCompletedVideo(videoUrl, filename) {
    processingOverlay.classList.add("hidden");
    playerPlaceholder.classList.add("hidden");
    videoPlayer.src = videoUrl;
    videoPlayer.classList.remove("hidden");
    videoPlayer.load();
    videoPlayer.play().catch(() => {});

    currentVideoFilename = filename || (videoUrl ? videoUrl.split("/").pop() : "super_video.mp4");
    btnDownload.href = `/api/download/${encodeURIComponent(currentVideoFilename)}`;
    btnDownload.download = currentVideoFilename;
    btnDownload.classList.remove("hidden");

    if (currentVideoFilename) {
      fileInfoBox.classList.remove("hidden");
      savedPathLabel.textContent = `outputs/${currentVideoFilename}`;
    }

    if (scenes[activeSceneIndex]) {
      scenes[activeSceneIndex].videoUrl = videoUrl;
      scenes[activeSceneIndex].filename = currentVideoFilename;
      scenes[activeSceneIndex].status = "ready";
      renderScenesTabs();
      renderScenePlayerBar();
    }

    playerBadge.textContent = "Terminé ✓";
    playerBadge.className = "text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium";
  }

  btnDownload.addEventListener("click", async (e) => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.save_video && currentVideoFilename) {
      e.preventDefault();
      try {
        const res = await window.pywebview.api.save_video(currentVideoFilename);
        if (res && res.success && res.saved_path) {
          savedPathLabel.textContent = res.saved_path;
        }
      } catch (err) {
        console.error("Erreur sauvegarde Desktop:", err);
        window.location.href = `/api/download/${encodeURIComponent(currentVideoFilename)}`;
      }
    }
  });

  if (btnRevealFolder) {
    btnRevealFolder.addEventListener("click", async () => {
      if (!currentVideoFilename) return;
      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.reveal_in_folder) {
          await window.pywebview.api.reveal_in_folder(currentVideoFilename);
        } else {
          await fetch(`/api/reveal/${encodeURIComponent(currentVideoFilename)}`, { method: "POST" });
        }
      } catch (err) {
        console.error("Erreur ouverture dossier:", err);
      }
    });
  }

  // Ajustement dynamique de hauteur selon le ratio réel de la vidéo chargée
  videoPlayer.addEventListener("loadedmetadata", () => {
    if (videoPlayer.videoWidth && videoPlayer.videoHeight && playerContainer) {
      const ratio = videoPlayer.videoWidth / videoPlayer.videoHeight;
      if (ratio < 0.75) {
        // Vidéo verticale 9:16 (format TikTok / Reel)
        playerContainer.style.minHeight = "480px";
      } else if (ratio > 1.45) {
        // Format panoramique 16:9
        playerContainer.style.minHeight = "340px";
      } else {
        // Format carré 1:1 ou 3:4 / 4:3
        playerContainer.style.minHeight = "420px";
      }
    }
  });

  function finishProcessing(success) {
    btnGenerate.disabled = false;
    if (btnGenerateAllScenes) btnGenerateAllScenes.disabled = false;
    updateGenerateButtonLabels();

    if (!success) {
      processingOverlay.classList.add("hidden");
      playerPlaceholder.classList.remove("hidden");
      playerBadge.textContent = "Erreur";
      playerBadge.className = "text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-medium";
    }
  }

  // 8. Historique Local des Créations
  async function loadHistory() {
    try {
      const res = await fetch("/api/history");
      const data = await res.json();
      if (data.success && data.history && data.history.length > 0) {
        renderHistory(data.history);
      } else {
        historyGrid.innerHTML = `
          <div class="col-span-full py-8 text-center text-slate-500 text-xs">
            Aucune vidéo générée pour le moment.
          </div>
        `;
      }
    } catch (e) {
      console.error("Erreur chargement historique:", e);
    }
  }

  function renderHistory(items) {
    historyGrid.innerHTML = "";
    items.forEach(item => {
      const card = document.createElement("div");
      card.className = "video-card-thumb group";
      card.innerHTML = `
        <video src="${item.video_url}" muted preload="metadata" onmouseover="this.play()" onmouseout="this.pause()"></video>
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-2 opacity-90 group-hover:opacity-100 transition-opacity">
          <span class="text-[10px] font-mono text-slate-300 truncate w-full">${item.filename}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        showCompletedVideo(item.video_url, item.filename);
      });
      historyGrid.appendChild(card);
    });
  }

  // ==========================================
  // GESTION DES MISES À JOUR (GITHUB)
  // ==========================================
  async function checkForUpdates(silent = false) {
    if (!silent) {
      updateModal.classList.remove("hidden");
      updateCheckLoading.classList.remove("hidden");
      updateContent.classList.add("hidden");
    }

    try {
      const res = await fetch("/api/updates/check");
      const data = await res.json();

      if (data.update_available) {
        updateNotificationDot.classList.remove("hidden");

        if (!silent) {
          updateStatusBanner.className = "p-3.5 rounded-xl border flex items-start gap-3 bg-amber-500/10 border-amber-500/30";
          updateStatusIcon.textContent = "🔔";
          updateStatusTitle.textContent = "Nouvelle mise à jour disponible !";
          updateStatusTitle.className = "text-xs font-bold text-amber-300";
          updateStatusDesc.textContent = "Une nouvelle version avec des améliorations est disponible sur GitHub.";

          btnApplyUpdate.classList.remove("hidden");
          btnApplyUpdate.disabled = false;
        }
      } else {
        updateNotificationDot.classList.add("hidden");

        if (!silent) {
          updateStatusBanner.className = "p-3.5 rounded-xl border flex items-start gap-3 bg-emerald-500/10 border-emerald-500/30";
          updateStatusIcon.textContent = "✅";
          updateStatusTitle.textContent = "Votre application est à jour";
          updateStatusTitle.className = "text-xs font-bold text-emerald-400";
          updateStatusDesc.textContent = "Vous utilisez déjà la dernière version publiée sur GitHub.";

          btnApplyUpdate.classList.add("hidden");
        }
      }

      if (!silent) {
        currentVersionTag.textContent = data.current_version || "v1.0";
        latestVersionTag.textContent = data.latest_version || "Dernière";

        if (data.latest_message) {
          updateMessageContainer.classList.remove("hidden");
          updateCommitMsg.textContent = `"${data.latest_message}"`;
        } else {
          updateMessageContainer.classList.add("hidden");
        }

        updateCheckLoading.classList.add("hidden");
        updateContent.classList.remove("hidden");
      }
    } catch (err) {
      console.warn("Échec de vérification des mises à jour:", err);
      if (!silent) {
        updateCheckLoading.classList.add("hidden");
        updateContent.classList.remove("hidden");
        updateStatusBanner.className = "p-3.5 rounded-xl border flex items-start gap-3 bg-rose-500/10 border-rose-500/30";
        updateStatusIcon.textContent = "⚠️";
        updateStatusTitle.textContent = "Connexion impossible";
        updateStatusTitle.className = "text-xs font-bold text-rose-400";
        updateStatusDesc.textContent = "Impossible de joindre GitHub. Vérifiez votre connexion Internet.";
        btnApplyUpdate.classList.add("hidden");
      }
    }
  }

  async function applySoftwareUpdate() {
    const updateProgressBar = document.getElementById("updateProgressBar");
    btnApplyUpdate.disabled = true;
    btnApplyUpdate.classList.add("opacity-50", "cursor-not-allowed");
    btnCancelUpdate.disabled = true;
    btnRecheckUpdate.disabled = true;
    updateProgressBox.classList.remove("hidden");

    if (updateProgressBar) {
      updateProgressBar.classList.remove("animate-pulse");
      updateProgressBar.style.transition = "width 0.4s ease";
      updateProgressBar.style.width = "25%";
    }
    updateProgressLabel.textContent = "Mise à jour du logiciel : téléchargement des nouveautés (25%)...";

    const stepTimer = setTimeout(() => {
      if (updateProgressBar) updateProgressBar.style.width = "65%";
      updateProgressLabel.textContent = "Mise à jour du logiciel : installation des fichiers (65%)...";
    }, 700);

    try {
      const res = await fetch("/api/updates/apply", { method: "POST" });
      clearTimeout(stepTimer);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Échec de l'installation de la mise à jour");
      }

      if (updateProgressBar) updateProgressBar.style.width = "100%";
      updateProgressLabel.textContent = "Mise à jour terminée (100%) ! Redémarrage du logiciel...";
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err) {
      clearTimeout(stepTimer);
      alert("Erreur lors de la mise à jour : " + err.message);
      btnApplyUpdate.disabled = false;
      btnApplyUpdate.classList.remove("opacity-50", "cursor-not-allowed");
      btnCancelUpdate.disabled = false;
      btnRecheckUpdate.disabled = false;
      updateProgressBox.classList.add("hidden");
    }
  }

  btnOpenUpdates.addEventListener("click", () => checkForUpdates(false));
  btnCloseUpdateModal.addEventListener("click", () => updateModal.classList.add("hidden"));
  btnCancelUpdate.addEventListener("click", () => updateModal.classList.add("hidden"));
  btnRecheckUpdate.addEventListener("click", () => checkForUpdates(false));
  btnApplyUpdate.addEventListener("click", applySoftwareUpdate);

  // Initialisation du Storyboard et premier onglet
  renderScenesTabs();
  loadSceneInputs(0);
  updateTotalDurationBadge();

  btnRefreshHistory.addEventListener("click", loadHistory);
});

