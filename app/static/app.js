// Super Video - Client Application Logic

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

  // État local
  let currentStudioMode = "motion"; // "motion" ou "cinema"
  let currentCamera = "push_in";
  let currentImageUrl = null;
  let currentLocalImagePath = null;
  let currentRatio = "original";
  let detectedImagePreset = null;
  let activeEventSource = null;

  // 1. Initialisation : vérifier la clé API et charger l'historique
  checkApiKeyStatus();
  loadHistory();

  // Gestion du changement de fournisseur
  if (selectProvider) {
    selectProvider.addEventListener("change", () => {
      if (selectProvider.value === "custom") {
        customUrlContainer.classList.remove("hidden");
        inputBaseUrl.focus();
      } else {
        customUrlContainer.classList.add("hidden");
        inputBaseUrl.value = selectProvider.value;
      }
    });
  }

  // 2. Gestion de la clé API et des fournisseurs
  async function checkApiKeyStatus() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      if (data.configured) {
        apiKeyDot.className = "w-2 h-2 rounded-full bg-emerald-400";
        apiKeyText.textContent = `Clé : ${data.masked_key}`;
      } else {
        apiKeyDot.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
        apiKeyText.textContent = "Clé non configurée";
      }

      if (data.base_url) {
        inputBaseUrl.value = data.base_url;
        if (!data.is_agnes_default) {
          selectProvider.value = "custom";
          customUrlContainer.classList.remove("hidden");
        } else {
          selectProvider.value = data.base_url;
          customUrlContainer.classList.add("hidden");
        }
      }
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

  btnSaveApiKey.addEventListener("click", async () => {
    const key = inputApiKey.value.trim();
    const chosenUrl = selectProvider.value === "custom" 
      ? inputBaseUrl.value.trim() 
      : selectProvider.value;

    const payload = {};
    if (key) payload.api_key = key;
    if (chosenUrl) payload.base_url = chosenUrl;

    if (!payload.api_key && !payload.base_url) {
      showAlert(apiKeyAlert, "Veuillez renseigner les champs nécessaires.", "error");
      return;
    }

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showAlert(apiKeyAlert, "Paramètres enregistrés avec succès !", "success");
        checkApiKeyStatus();
        inputApiKey.value = "";
        setTimeout(closeSettings, 1200);
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

  // 5. Durée Slider
  durationSlider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value).toFixed(1);
    durationValue.textContent = `${val}s`;
    generateBtnText.textContent = currentStudioMode === "motion" 
      ? `Générer le Motion Design (${val}s)`
      : `Générer la vidéo (${val}s)`;
  });

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

  // 7. Génération de Vidéo
  btnGenerate.addEventListener("click", async () => {
    if (!currentImageUrl) {
      alert("Veuillez charger une image source à animer.");
      return;
    }

    let prompt = "";
    const isMotionDesign = currentStudioMode === "motion";

    if (isMotionDesign) {
      prompt = compileMotionDesignPrompt();
    } else {
      prompt = cinemaPromptInput ? cinemaPromptInput.value.trim() : "";
      if (!prompt) {
        alert("Veuillez saisir une description de la scène cinématographique ou choisir un preset.");
        if (cinemaPromptInput) cinemaPromptInput.focus();
        return;
      }
    }

    // Désactivation du bouton
    btnGenerate.disabled = true;
    generateBtnText.textContent = "Lancement de la tâche...";
    playerBadge.textContent = "Génération...";
    playerBadge.className = "text-xs px-2 py-0.5 rounded-full bg-brand-violet/20 text-brand-purple font-medium";

    // Affichage de l'overlay de processing
    playerPlaceholder.classList.add("hidden");
    videoPlayer.classList.add("hidden");
    btnDownload.classList.add("hidden");
    fileInfoBox.classList.add("hidden");
    processingOverlay.classList.remove("hidden");
    updateProgress(5, "Initialisation du moteur Super Video AI...");

    try {
      // Calcul des dimensions exactes pour garantir zéro coupure de tête ou de trophée
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

      const payload = {
        prompt: prompt,
        image_url: currentImageUrl,
        model: modelSelect.value,
        mode: "keyframe",
        seconds: String(durationSlider.value),
        size: sizeSelect.value,
        aspect_ratio: currentRatio,
        target_width: targetWidth,
        target_height: targetHeight,
        motion_design_mode: isMotionDesign
      };

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
      startProgressStream(videoId, modelSelect.value);

    } catch (err) {
      alert("Erreur de génération : " + err.message);
      finishProcessing(false);
    }
  });

  function startProgressStream(videoId, modelName) {
    if (activeEventSource) {
      activeEventSource.close();
    }

    updateProgress(15, "Tâche transmise au moteur Super Video AI. Analyse du visuel...");

    activeEventSource = new EventSource(`/api/stream/${videoId}?model=${encodeURIComponent(modelName)}`);

    activeEventSource.onmessage = (event) => {
      try {
        const info = JSON.parse(event.data);

        if (info.status === "completed") {
          updateProgress(100, "Téléchargement local du fichier MP4 terminé !");
          activeEventSource.close();
          setTimeout(() => {
            showCompletedVideo(info.local_url, info.filename);
            loadHistory();
            finishProcessing(true);
          }, 800);
        } else if (info.status === "failed") {
          activeEventSource.close();
          alert("La génération a échoué : " + (info.error || "Raison inconnue"));
          finishProcessing(false);
        } else if (info.status === "in_progress") {
          const prog = Math.max(20, info.progress || 35);
          updateProgress(prog, `Calcul et rendu vidéo en cours (${prog}%)...`);
        } else if (info.status === "queued") {
          updateProgress(10, "En file d'attente sur les serveurs de rendu Super Video AI...");
        }
      } catch (e) {
        console.error("Erreur parsing SSE:", e);
      }
    };

    activeEventSource.onerror = () => {
      console.warn("Connexion flux interrompue.");
    };
  }

  function updateProgress(percent, statusMsg) {
    progressPercentageText.textContent = `${percent}%`;
    progressBarFill.style.width = `${percent}%`;
    processStatus.textContent = statusMsg;
  }

  function showCompletedVideo(videoUrl, filename) {
    processingOverlay.classList.add("hidden");
    videoPlayer.src = videoUrl;
    videoPlayer.classList.remove("hidden");
    videoPlayer.load();
    videoPlayer.play().catch(() => {});

    btnDownload.href = videoUrl;
    btnDownload.download = filename || "super_video.mp4";
    btnDownload.classList.remove("hidden");

    if (filename) {
      fileInfoBox.classList.remove("hidden");
      savedPathLabel.textContent = `outputs/${filename}`;
    }

    playerBadge.textContent = "Terminé ✓";
    playerBadge.className = "text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium";
  }

  function finishProcessing(success) {
    btnGenerate.disabled = false;
    const dur = parseFloat(durationSlider.value).toFixed(1);
    generateBtnText.textContent = `Générer la vidéo (${dur}s)`;

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
    btnApplyUpdate.disabled = true;
    btnApplyUpdate.classList.add("opacity-50", "cursor-not-allowed");
    btnCancelUpdate.disabled = true;
    btnRecheckUpdate.disabled = true;
    updateProgressBox.classList.remove("hidden");
    updateProgressLabel.textContent = "Téléchargement et application des fichiers...";

    try {
      const res = await fetch("/api/updates/apply", { method: "POST" });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Échec de l'installation de la mise à jour");
      }

      updateProgressLabel.textContent = "Mise à jour réussie ! Rechargement de l'application...";
      setTimeout(() => {
        window.location.reload();
      }, 1800);
    } catch (err) {
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

  // Vérification automatique et silencieuse au lancement du studio
  setTimeout(() => checkForUpdates(true), 2500);

  btnRefreshHistory.addEventListener("click", loadHistory);
});
