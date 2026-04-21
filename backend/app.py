import os
import json
import uuid
import tempfile
import subprocess
from openai import OpenAI
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from supabase import create_client, Client
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)

# Config depuis variables d'environnement
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BUCKET_CLIPS = "clips"
BUCKET_SOUNDS = "sounds"
BUCKET_OUTPUT = "output"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

ALLOWED_VIDEO = {"mp4", "mov", "avi"}
ALLOWED_AUDIO = {"mp3", "wav", "mp4", "m4a"}

def allowed_file(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

# ─── PAGES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/bibliotheque")
def bibliotheque():
    return render_template("bibliotheque.html")

@app.route("/creer")
def creer():
    return render_template("creer.html")

# ─── API CLIPS ────────────────────────────────────────────────────────────────

@app.route("/api/clips", methods=["GET"])
def get_clips():
    result = supabase.table("clips").select("*").order("created_at", desc=True).execute()
    return jsonify(result.data)

@app.route("/api/clips", methods=["POST"])
def upload_clip():
    if "file" not in request.files:
        return jsonify({"error": "Fichier manquant"}), 400
    file = request.files["file"]
    tags = request.form.get("tags", "")
    name = request.form.get("name", file.filename)

    if not allowed_file(file.filename, ALLOWED_VIDEO):
        return jsonify({"error": "Format non supporté, utilisez MP4"}), 400

    filename = f"{uuid.uuid4()}.mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            supabase.storage.from_(BUCKET_CLIPS).upload(filename, f, {"content-type": "video/mp4"})

    tags_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    supabase.table("clips").insert({
        "id": str(uuid.uuid4()),
        "name": name,
        "filename": filename,
        "tags": tags_list
    }).execute()

    os.unlink(tmp.name)
    return jsonify({"success": True, "message": f"Clip '{name}' ajouté avec succès"})

@app.route("/api/clips/<clip_id>", methods=["DELETE"])
def delete_clip(clip_id):
    clip = supabase.table("clips").select("*").eq("id", clip_id).single().execute()
    if clip.data:
        supabase.storage.from_(BUCKET_CLIPS).remove([clip.data["filename"]])
        supabase.table("clips").delete().eq("id", clip_id).execute()
    return jsonify({"success": True})

# ─── API SONS ─────────────────────────────────────────────────────────────────

@app.route("/api/sounds", methods=["GET"])
def get_sounds():
    result = supabase.table("sounds").select("*").execute()
    return jsonify(result.data)

@app.route("/api/sounds", methods=["POST"])
def upload_sound():
    if "file" not in request.files:
        return jsonify({"error": "Fichier manquant"}), 400
    file = request.files["file"]
    sound_type = request.form.get("type", "whoosh")  # "intro" ou "whoosh"
    name = request.form.get("name", file.filename)

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            supabase.storage.from_(BUCKET_SOUNDS).upload(filename, f)

    supabase.table("sounds").insert({
        "id": str(uuid.uuid4()),
        "name": name,
        "filename": filename,
        "type": sound_type
    }).execute()

    os.unlink(tmp.name)
    return jsonify({"success": True})

# ─── API GÉNÉRATION VIDÉO ─────────────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def generate_video():
    data = request.json
    script = data.get("script", "").strip()
    voiceover_filename = data.get("voiceover_filename", "")

    if not script:
        return jsonify({"error": "Script manquant"}), 400

    # 1. Récupérer tous les clips de la bibliothèque
    clips_result = supabase.table("clips").select("*").execute()
    clips = clips_result.data
    if not clips:
        return jsonify({"error": "Aucun clip dans la bibliothèque"}), 400

    # 2. IA : matcher script → clips
    clips_info = "\n".join([f"- ID:{c['id']} | Nom:{c['name']} | Tags:{', '.join(c['tags'])}" for c in clips])
    prompt = f"""Tu es un assistant de montage vidéo TikTok spécialisé dans la niche scooter/moto 50cc.

Voici le script de la voix off :
"{script}"

Voici la bibliothèque de clips disponibles :
{clips_info}

Ta mission :
1. Découpe le script en segments logiques de ~5 secondes chacun (10 à 12 segments pour ~60 secondes)
2. Pour chaque segment, choisis le clip dont les tags correspondent le mieux aux mots et au sens du segment
3. Un clip peut être utilisé plusieurs fois si nécessaire
4. Priorise la pertinence sémantique entre le texte et les tags

Réponds UNIQUEMENT en JSON valide sans markdown ni backticks :
{{
  "segments": [
    {{"segment": "texte du segment", "clip_id": "id_du_clip", "clip_name": "nom_du_clip", "reason": "pourquoi ce clip"}}
  ]
}}"""

<<<<<<< HEAD
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
=======
    response = anthropic_client.messages.create(
        model="claude-3-opus-20240229",
>>>>>>> 6fd7bd3bc6fcf9d8c836eba8050313cd369df077
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = response.choices[0].message.content.strip()
    result_text = result_text.replace("```json", "").replace("```", "").strip()
    matching = json.loads(result_text)
    segments = matching["segments"]

    # 3. Télécharger les fichiers nécessaires
    tmpdir = tempfile.mkdtemp()
    downloaded_clips = {}

    for seg in segments:
        clip_id = seg["clip_id"]
        if clip_id not in downloaded_clips:
            clip = next((c for c in clips if c["id"] == clip_id), None)
            if clip:
                clip_path = os.path.join(tmpdir, f"clip_{clip_id}.mp4")
                file_bytes = supabase.storage.from_(BUCKET_CLIPS).download(clip["filename"])
                with open(clip_path, "wb") as f:
                    f.write(file_bytes)
                downloaded_clips[clip_id] = clip_path

    # 4. Télécharger les sons
    sounds_result = supabase.table("sounds").select("*").execute()
    sounds = sounds_result.data
    intro_sounds = [s for s in sounds if s["type"] == "intro"]
    whoosh_sounds = [s for s in sounds if s["type"] == "whoosh"]

    intro_path = None
    whoosh_paths = []

    if intro_sounds:
        s = intro_sounds[0]
        ext = s["filename"].rsplit(".", 1)[1]
        p = os.path.join(tmpdir, f"intro.{ext}")
        file_bytes = supabase.storage.from_(BUCKET_SOUNDS).download(s["filename"])
        with open(p, "wb") as f:
            f.write(file_bytes)
        intro_path = p

    for i, s in enumerate(whoosh_sounds[:3]):
        ext = s["filename"].rsplit(".", 1)[1]
        p = os.path.join(tmpdir, f"whoosh_{i}.{ext}")
        file_bytes = supabase.storage.from_(BUCKET_SOUNDS).download(s["filename"])
        with open(p, "wb") as f:
            f.write(file_bytes)
        whoosh_paths.append(p)

    # 5. Télécharger la voix off
    voiceover_path = None
    if voiceover_filename:
        vo_ext = voiceover_filename.rsplit(".", 1)[1]
        voiceover_path = os.path.join(tmpdir, f"voiceover.{vo_ext}")
        file_bytes = supabase.storage.from_(BUCKET_SOUNDS).download(voiceover_filename)
        with open(voiceover_path, "wb") as f:
            f.write(file_bytes)

    # 6. Assembler avec FFmpeg
    output_path = os.path.join(tmpdir, "output.mp4")
    _assemble_video(segments, downloaded_clips, intro_path, whoosh_paths, voiceover_path, output_path, tmpdir)

    # 7. Upload résultat sur Supabase
    output_filename = f"output_{uuid.uuid4()}.mp4"
    with open(output_path, "rb") as f:
        supabase.storage.from_(BUCKET_OUTPUT).upload(output_filename, f, {"content-type": "video/mp4"})

    # URL publique
    url_result = supabase.storage.from_(BUCKET_OUTPUT).get_public_url(output_filename)

    # Nettoyer tmpdir
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    return jsonify({
        "success": True,
        "segments": segments,
        "download_url": url_result,
        "filename": output_filename
    })


def _assemble_video(segments, downloaded_clips, intro_path, whoosh_paths, voiceover_path, output_path, tmpdir):
    clip_paths = []

    for i, seg in enumerate(segments):
        clip_id = seg["clip_id"]
        src = downloaded_clips.get(clip_id)
        if not src:
            continue

        trimmed = os.path.join(tmpdir, f"seg_{i}.mp4")

        if i == 0:
            # Premier clip : effet shake rapide et violent
            shake_filter = (
                "crop=iw-40:ih-40:x='40*sin(t*80)':y='40*cos(t*80)',"
                "scale=iw+40:ih+40,"
                "crop=iw-40:ih-40"
            )
            cmd = [
                "ffmpeg", "-y", "-i", src,
                "-t", "5",
                "-vf", shake_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-an", trimmed
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", src,
                "-t", "5",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-an", trimmed
            ]

        subprocess.run(cmd, check=True, capture_output=True)
        clip_paths.append(trimmed)

    # Concaténer les clips
    concat_list = os.path.join(tmpdir, "concat.txt")
    with open(concat_list, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p}'\n")

    silent_video = os.path.join(tmpdir, "silent.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        silent_video
    ], check=True, capture_output=True)

    # Construire la piste audio avec whoosh entre clips et intro au début
    audio_inputs = []
    audio_filter_parts = []
    input_idx = 0

    # Vidéo silencieuse en entrée 0
    main_inputs = ["-i", silent_video]

    # Voix off
    if voiceover_path:
        main_inputs += ["-i", voiceover_path]
        vo_idx = 1
        input_idx = 2
    else:
        vo_idx = None
        input_idx = 1

    # Son intro
    if intro_path:
        main_inputs += ["-i", intro_path]
        intro_idx = input_idx
        input_idx += 1
    else:
        intro_idx = None

    # Whoosh sounds
    whoosh_indices = []
    for wp in whoosh_paths:
        main_inputs += ["-i", wp]
        whoosh_indices.append(input_idx)
        input_idx += 1

    # Construire le filtre audio complexe
    filter_parts = []
    mix_inputs = []

    if vo_idx is not None:
        filter_parts.append(f"[{vo_idx}:a]volume=1.0[vo]")
        mix_inputs.append("[vo]")

    if intro_idx is not None:
        filter_parts.append(f"[{intro_idx}:a]adelay=0|0,volume=0.8[intro]")
        mix_inputs.append("[intro]")

    # Whoosh à chaque transition (toutes les 5 secondes)
    for i in range(1, len(clip_paths)):
        delay_ms = i * 5000
        if whoosh_indices:
            wi = whoosh_indices[i % len(whoosh_indices)]
            label = f"[w{i}]"
            filter_parts.append(f"[{wi}:a]adelay={delay_ms}|{delay_ms},volume=0.7{label}")
            mix_inputs.append(label)

    if mix_inputs:
        n = len(mix_inputs)
        all_mix = "".join(mix_inputs)
        filter_parts.append(f"{all_mix}amix=inputs={n}:duration=longest[aout]")
        audio_filter = ";".join(filter_parts)

        cmd_final = (
            ["ffmpeg", "-y"] +
            main_inputs +
            ["-filter_complex", audio_filter,
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             output_path]
        )
    else:
        cmd_final = [
            "ffmpeg", "-y", "-i", silent_video,
            "-c:v", "copy", "-an",
            output_path
        ]

    subprocess.run(cmd_final, check=True, capture_output=True)


# ─── UPLOAD VOIX OFF ──────────────────────────────────────────────────────────

@app.route("/api/voiceover", methods=["POST"])
def upload_voiceover():
    if "file" not in request.files:
        return jsonify({"error": "Fichier manquant"}), 400
    file = request.files["file"]
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"voiceover_{uuid.uuid4()}.{ext}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            supabase.storage.from_(BUCKET_SOUNDS).upload(filename, f)
    os.unlink(tmp.name)

    return jsonify({"success": True, "filename": filename})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
