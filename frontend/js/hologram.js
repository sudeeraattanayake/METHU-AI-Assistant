
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const container = document.getElementById("hologram-scene");

if (container) {
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0, 4);

    const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true
    });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 2));

    const light = new THREE.DirectionalLight(0x88ddff, 3);
    light.position.set(2, 3, 4);
    scene.add(light);

    let avatar = null;
    let headBone = null;
    let faceMesh = null;

    // Voice lip-sync state
    let isSpeaking = false;
    let audioAnalyser = null;
    let audioData = null;
    let currentJawOpen = 0;

    function setFacialMorph(name, value) {
        if (!faceMesh?.morphTargetDictionary) return;

        const index = faceMesh.morphTargetDictionary[name];

        if (index !== undefined) {
            faceMesh.morphTargetInfluences[index] =
                THREE.MathUtils.clamp(value, 0, 1);
        }
    }

    function animateBlink(time) {
        const phase = (time % 4000) / 4000;
        let blink = 0;

        if (phase > 0.94) {
            const progress = (phase - 0.94) / 0.06;
            blink = Math.sin(progress * Math.PI);
        }

        setFacialMorph("eyeBlinkLeft", blink);
        setFacialMorph("eyeBlinkRight", blink);
    }

    // Listen for audio playback events
    window.addEventListener("methu:speech-start", () => {
        isSpeaking = true;
        console.log("METHU Lip-Sync Started");
    });

    window.addEventListener("methu:speech-end", () => {
        isSpeaking = false;
        console.log("METHU Lip-Sync Stopped");
    });

    // Receives an analyser from voice.js
    window.addEventListener("methu:audio-analyser", (event) => {
        audioAnalyser = event.detail.analyser;
        audioData = new Uint8Array(
            audioAnalyser.fftSize
        );
    });

    function animateMouth() {
        let targetJaw = 0;

        if (isSpeaking && audioAnalyser && audioData) {
            audioAnalyser.getByteTimeDomainData(audioData);

            let sum = 0;

            for (let i = 0; i < audioData.length; i++) {
                const sample = (audioData[i] - 128) / 128;
                sum += sample * sample;
            }

            const rms = Math.sqrt(sum / audioData.length);

            // Map speech volume to mouth opening
            targetJaw = THREE.MathUtils.clamp(
                (rms - 0.03) * 2.2,
                0,
                0.18
            );;
        }

        // Smooth mouth movement
        currentJawOpen = THREE.MathUtils.lerp(
            currentJawOpen,
            targetJaw,
            0.10
        );

        setFacialMorph("jawOpen", currentJawOpen);
        setFacialMorph("mouthFunnel", currentJawOpen * 0.12);
        setFacialMorph("mouthPucker", currentJawOpen * 0.06);
    }

    const loader = new GLTFLoader();

    loader.load(
        "assets/models/model.glb",
        (gltf) => {
            avatar = gltf.scene;
            headBone = avatar.getObjectByName("head");

            if (headBone) {
                console.log(
                    "METHU Head Bone Found:",
                    headBone.name
                );
            } else {
                console.warn("METHU Head Bone Not Found");
            }

            scene.add(avatar);

            avatar.traverse((object) => {
                if (
                    object.isMesh &&
                    object.morphTargetDictionary &&
                    "eyeBlinkLeft" in object.morphTargetDictionary
                ) {
                    faceMesh = object;
                }
            });

            const bounds = new THREE.Box3().setFromObject(avatar);
            const center = bounds.getCenter(new THREE.Vector3());
            const size = bounds.getSize(new THREE.Vector3());

            avatar.position.sub(center);

            const maxDimension = Math.max(
                size.x,
                size.y,
                size.z
            );

            if (maxDimension > 0) {
                avatar.scale.setScalar(2.5 / maxDimension);
                avatar.position.multiplyScalar(
                    2.5 / maxDimension
                );
            }

            console.log("METHU Avatar Loaded Successfully");

            avatar.traverse((object) => {
                if (object.isMesh) {
                    console.log("Mesh:", object.name);

                    if (object.morphTargetDictionary) {
                        console.log(
                            "Facial Morph Targets:",
                            Object.keys(object.morphTargetDictionary)
                        );
                    }

                    if (object.isSkinnedMesh) {
                        console.log(
                            "Bones:",
                            object.skeleton.bones.map(
                                (bone) => bone.name
                            )
                        );
                    }
                }
            });

            console.log(
                "Available GLB Animations:",
                gltf.animations.map(
                    (animation) => animation.name
                )
            );
        },
        undefined,
        (error) => {
            console.error(
                "METHU Avatar Loading Error:",
                error
            );
        }
    );

    function resize() {
        const width = container.clientWidth || 600;
        const height = container.clientHeight || 420;

        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    }

    window.addEventListener("resize", resize);
    resize();

    function animate(time) {
        if (avatar && headBone) {
            const t = time * 0.001;

            // Gentle head movement
            headBone.rotation.y = Math.sin(t * 0.7) * 0.15;
            headBone.rotation.x = Math.sin(t * 0.45) * 0.06;
            headBone.rotation.z = Math.sin(t * 0.55) * 0.04;
        }

        animateBlink(time);
        animateMouth();

        renderer.render(scene, camera);
    }

    renderer.setAnimationLoop(animate);
}
