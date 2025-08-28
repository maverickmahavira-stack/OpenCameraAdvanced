#!/usr/bin/env python3
# Applies Pro Video (10-bit LOG) changes into the checked-out OpenCamera tree.

import re
from pathlib import Path

root = Path(".")
def read(p): return Path(p).read_text(encoding="utf-8", errors="ignore")
def write(p, s): Path(p).parent.mkdir(parents=True, exist_ok=True); Path(p).write_text(s, encoding="utf-8")

egl = root / "src/com/almalence/opencam/ui/EglEncoder.java"
dro = root / "src/com/almalence/plugins/capture/video/DROVideoEngine.java"
cam = root / "src/com/almalence/opencam/cameracontroller/Camera2Controller.java"
pref_main = root / "res/xml/preferences.xml"
pref_addon = root / "res/xml/opencamera_addon_prefs.xml"
arrays = root / "res/values/arrays_opencamera_addon.xml"

# 1) EglEncoder.java: add Pro toggle, profiles, HDR, HEVC Main10 when Pro is ON, shader variants
if egl.exists():
    s = read(egl)
    if "setProVideoMode" not in s:
        s = s.replace("public class EglEncoder implements Runnable {",
                      "public class EglEncoder implements Runnable {\n"
                      "    private static boolean sProVideo = false;\n"
                      "    public static void setProVideoMode(boolean enabled){ sProVideo = enabled; }\n"
                      "    private static int sProfile = 1; // 1=Canon,2=ARRI,3=ACES,4=Flat\n"
                      "    public static void setLogProfile(int p){ sProfile = p; }\n"
                      "    private static int sHdrTransfer = 0; // 0=SDR,1=HLG,2=PQ\n"
                      "    public static void setHdrTransfer(int v){ sHdrTransfer = v; }\n")
    s = s.replace("SHADER_FRAGMENT\t\t\t\t=", "SHADER_FRAGMENT_PRO\t\t\t\t=")
    if "SHADER_FRAGMENT_CANON" not in s:
        s = s.replace('";\n\n\tprivate static final FloatBuffer\tVERTEX_BUFFER;',
        '";\n\n\tprivate static final String SHADER_FRAGMENT_CANON = "#extension GL_OES_EGL_image_external:enable\\n" +'
        '"precision mediump float;\\n" + "uniform samplerExternalOES sTexture;\\n" + "varying vec2 v_TexCoordinate;\\n" +'
        '"float log10p(float x){ return log(x)/log(10.0); }\\n" + "vec3 toLinear(vec3 c){ return pow(c, vec3(2.2)); }\\n" +'
        '"vec3 mulMat(vec3 v, mat3 m){ return vec3(dot(v, m[0]), dot(v, m[1]), dot(v, m[2])); }\\n" +'
        '"const mat3 M_lin_to_CanonCinema = mat3(0.7161046,0.1009296,0.1471858, 0.2581874,0.7249378,0.0168748, 0.0,0.0517813,0.7448387);\\n" +'
        '"float canonLog3Encode(float L){ if(L<0.011361){ return (L*5.555556)+0.092864; } else { return (log10p(L*0.3584+0.00873)*0.241514)+0.598206; } }\\n" +'
        '"void main(){ vec3 rgb=texture2D(sTexture,v_TexCoordinate).rgb; vec3 lin=toLinear(rgb); vec3 ccg=mulMat(lin,M_lin_to_CanonCinema);'
        ' vec3 logv=vec3(canonLog3Encode(ccg.r),canonLog3Encode(ccg.g),canonLog3Encode(ccg.b)); gl_FragColor=vec4(logv,1.0);}";\n'
        '\tprivate static final String SHADER_FRAGMENT_ARRI = "#extension GL_OES_EGL_image_external:enable\\n" +'
        '"precision mediump float;\\n" + "uniform samplerExternalOES sTexture;\\n" + "varying vec2 v_TexCoordinate;\\n" +'
        '"float log10p(float x){ return log(x)/log(10.0); }\\n" + "vec3 toLinear(vec3 c){ return pow(c, vec3(2.2)); }\\n" +'
        '"vec3 mulMat(vec3 v, mat3 m){ return vec3(dot(v, m[0]), dot(v, m[1]), dot(v, m[2])); }\\n" +'
        '"const mat3 M_lin_to_AWG = mat3(0.638008,0.214704,0.097744, 0.291954,0.823841,-0.115795, 0.002798,0.062859,0.731717);\\n" +'
        '"float logC3Encode(float L){ float cut=0.010591; if(L>cut){ return (0.24719*log10p(5.555556*L+0.052272))+0.385537; } else { return (L*5.367655)+0.092809; } }\\n" +'
        '"void main(){ vec3 rgb=texture2D(sTexture,v_TexCoordinate).rgb; vec3 lin=toLinear(rgb); vec3 awg=mulMat(lin,M_lin_to_AWG);'
        ' vec3 logv=vec3(logC3Encode(awg.r),logC3Encode(awg.g),logC3Encode(awg.b)); gl_FragColor=vec4(logv,1.0);}";\n'
        '\tprivate static final String SHADER_FRAGMENT_ACES = "#extension GL_OES_EGL_image_external:enable\\n" +'
        '"precision mediump float;\\n" + "uniform samplerExternalOES sTexture;\\n" + "varying vec2 v_TexCoordinate;\\n" +'
        '"vec3 toLinear(vec3 c){ return pow(c, vec3(2.2)); }\\n" + "vec3 mulMat(vec3 v, mat3 m){ return vec3(dot(v, m[0]), dot(v, m[1]), dot(v, m[2])); }\\n" +'
        '"const mat3 M_lin_to_ACEScg = mat3(0.662454,0.134004,0.156188, 0.272229,0.674082,0.053689, -0.005574,0.004060,1.010339);\\n" +'
        '"float acescctEncode(float L){ float cut=0.0078125; if(L<cut){ return (10.540237*L)+0.072905; } else { return (log2(L+0.072905)+9.72)/17.52; } }\\n" +'
        '"void main(){ vec3 rgb=texture2D(sTexture,v_TexCoordinate).rgb; vec3 lin=toLinear(rgb); vec3 ap1=mulMat(lin,M_lin_to_ACEScg);'
        ' vec3 logv=vec3(acescctEncode(ap1.r),acescctEncode(ap1.g),acescctEncode(ap1.b)); gl_FragColor=vec4(logv,1.0);}";\n'
        '\tprivate static final String SHADER_FRAGMENT_FLAT = "#extension GL_OES_EGL_image_external:enable\\n" +'
        '"precision mediump float;\\n" + "uniform samplerExternalOES sTexture;\\n" + "varying vec2 v_TexCoordinate;\\n" +'
        '"void main(){ vec3 rgb=texture2D(sTexture,v_TexCoordinate).rgb; vec3 flat=pow(rgb, vec3(0.85)); gl_FragColor=vec4(flat,1.0);}";\n\n'
        '\tprivate static final String SHADER_FRAGMENT_STOCK = "#extension GL_OES_EGL_image_external:enable\\n" + "precision mediump float;\\n" + "uniform samplerExternalOES sTexture;\\n" + "varying vec2 v_TexCoordinate;\\n" + "void main(){ gl_FragColor = texture2D(sTexture, v_TexCoordinate); }";\n\n'
        '\tprivate static final FloatBuffer\tVERTEX_BUFFER;')
    s = s.replace('loadShader(SHADER_VERTEX, SHADER_FRAGMENT_PRO)',
                  'loadShader(SHADER_VERTEX, (sProfile==1?SHADER_FRAGMENT_CANON:sProfile==2?SHADER_FRAGMENT_ARRI:sProfile==3?SHADER_FRAGMENT_ACES:SHADER_FRAGMENT_FLAT))')
    s = s.replace('loadShader(SHADER_VERTEX_WITH_ROTATION, SHADER_FRAGMENT_PRO)',
                  'loadShader(SHADER_VERTEX_WITH_ROTATION, (sProfile==1?SHADER_FRAGMENT_CANON:sProfile==2?SHADER_FRAGMENT_ARRI:sProfile==3?SHADER_FRAGMENT_ACES:SHADER_FRAGMENT_FLAT))')
    if 'final String mime = sProVideo ? "video/hevc" : MIME_TYPE;' not in s:
        s = s.replace('final MediaCodecInfo codecInfo = selectCodec(MIME_TYPE);',
                      'final String mime = sProVideo ? "video/hevc" : MIME_TYPE;\n        final MediaCodecInfo codecInfo = selectCodec(mime);')
        s = s.replace('final MediaFormat format = MediaFormat.createVideoFormat(MIME_TYPE, this.mWidth, this.mHeight);',
                      'final MediaFormat format = MediaFormat.createVideoFormat(mime, this.mWidth, this.mHeight);')
        s = s.replace('format.setInteger(MediaFormat.KEY_PUSH_BLANK_BUFFERS_ON_STOP, 0);',
                      'format.setInteger(MediaFormat.KEY_PUSH_BLANK_BUFFERS_ON_STOP, 0);\n'
                      '        if (sProVideo) {\n'
                      '            try { format.setInteger(MediaFormat.KEY_PROFILE, 2); } catch (Throwable t) {}\n'
                      '            try { format.setInteger(MediaFormat.KEY_COLOR_STANDARD, MediaFormat.COLOR_STANDARD_BT2020); } catch (Throwable t) {}\n'
                      '            try {\n'
                      '                int xfer = (sHdrTransfer==2) ? 6 /*ST2084*/ : (sHdrTransfer==1 ? 7 /*HLG*/ : 3 /*SDR*/);\n'
                      '                format.setInteger(MediaFormat.KEY_COLOR_TRANSFER, xfer);\n'
                      '                format.setInteger(MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_LIMITED);\n'
                      '            } catch (Throwable t) {}\n'
                      '        }')
    write(egl, s)

# 2) DROVideoEngine.java: read prefs and set flags
if dro.exists():
    s = read(dro)
    if "PreferenceManager" not in s:
        s = s.replace('import javax.microedition.khronos.opengles.GL10;',
                      'import javax.microedition.khronos.opengles.GL10;\n'
                      'import android.content.SharedPreferences;\n'
                      'import android.preference.PreferenceManager;\n'
                      'import com.almalence.opencam.ui.EglEncoder;')
    if "pref_color_profile" not in s:
        s = s.replace('new EglEncoder(path, DROVideoEngine.this.previewWidth,',
            '{\n'
            'SharedPreferences sp = PreferenceManager.getDefaultSharedPreferences(ApplicationScreen.getMainContext());\n'
            'boolean pro = sp.getBoolean("pref_pro_video_mode", false);\n'
            'EglEncoder.setProVideoMode(pro);\n'
            'String prof = sp.getString("pref_color_profile", "canon_log3_cinema");\n'
            'int p = 1; if("arri_logc3_awg".equals(prof)) p=2; else if("acescct_acescg".equals(prof)) p=3; else if("flat_bt709".equals(prof)) p=4;\n'
            'EglEncoder.setLogProfile(p);\n'
            'String hdr = sp.getString("pref_hdr_delivery","none");\n'
            'int ht = 0; if("hlg".equals(hdr)) ht=1; else if("pq".equals(hdr)) ht=2;\n'
            'EglEncoder.setHdrTransfer(ht);\n'
            '}\n'
            'new EglEncoder(path, DROVideoEngine.this.previewWidth,')
    write(dro, s)

# 3) Camera2Controller.java: apply manual exposure/ISO/focus + WB CCT
if cam.exists():
    s = read(cam)
    if "applyLogManualIfEnabled" not in s:
        s = s.replace('package com.almalence.opencam.cameracontroller;',
                      'package com.almalence.opencam.cameracontroller;\n'
                      'import android.content.SharedPreferences;\n'
                      'import android.preference.PreferenceManager;\n'
                      'import com.almalence.ui.ApplicationScreen;\n'
                      'import com.example.opencamera_addon.CaptureTuning;\n'
                      'import android.hardware.camera2.params.RggbChannelVector;\n'
                      'import android.hardware.camera2.params.ColorSpaceTransform;')
        s += """
// --- Pro Video LOG manual controls + WB CCT ---
private void applyLogManualIfEnabled(CaptureRequest.Builder builder){
  try{
    SharedPreferences sp = PreferenceManager.getDefaultSharedPreferences(ApplicationScreen.getMainContext());
    if(sp.getBoolean("pref_pro_video_mode", false)){
      long exposureNs = 1000000000L/48L; int iso = 200; float focusDist = 1.0f/1.5f;
      try { exposureNs = Long.parseLong(sp.getString("pref_exposure_us","20833")) * 1000L; } catch(Throwable t) {}
      try { iso = Integer.parseInt(sp.getString("pref_iso","200")); } catch(Throwable t) {}
      try { float focusM = Float.parseFloat(sp.getString("pref_focus_m","1.5")); focusDist = 1.0f/Math.max(0.1f, focusM); } catch(Throwable t) {}
      com.example.opencamera_addon.CaptureTuning.applyFullManual(builder, exposureNs, iso, focusDist);
      String wbq = sp.getString("pref_wb_quick","custom");
      int cct = 5500;
      if(!"custom".equals(wbq)) { try { cct = Integer.parseInt(wbq); } catch(Throwable t) {} }
      else { try { cct = Integer.parseInt(sp.getString("pref_wb_cct","5500")); } catch(Throwable t) {} }
      builder.set(CaptureRequest.CONTROL_AWB_MODE, CameraMetadata.CONTROL_AWB_MODE_OFF);
      builder.set(CaptureRequest.COLOR_CORRECTION_MODE, CameraMetadata.COLOR_CORRECTION_MODE_TRANSFORM_MATRIX);
      builder.set(CaptureRequest.COLOR_CORRECTION_GAINS, gainsFromCct(cct));
      builder.set(CaptureRequest.COLOR_CORRECTION_TRANSFORM, new ColorSpaceTransform(new int[]{ 1,1,0,1,0,1, 0,1,1,1,0,1, 0,1,0,1,1,1 }));
    }
  }catch(Throwable t){}
}
/** Approx WB gains from CCT (K) */
private RggbChannelVector gainsFromCct(int cctK){
  try{
    double T = Math.max(1000, Math.min(12000, cctK));
    double n = (T - 6500.0) / 6500.0;
    double x = 0.31271 + (-0.000246481) * n + (0.00331328) * n*n + (-0.00327372) * n*n*n;
    double y = 2.87 * x - 3.0 * x * x - 0.275;
    double X = x / y, Y = 1.0, Z = (1 - x - y) / y;
    double r =  3.2406*X + -1.5372*Y + -0.4986*Z;
    double g = -0.9689*X +  1.8758*Y +  0.0415*Z;
    double b =  0.0557*X + -0.2040*Y +  1.0570*Z;
    r = Math.max(1e-4, r); g = Math.max(1e-4, g); b = Math.max(1e-4, b);
    double gainR = 1.0 / r, gainG = 1.0 / g, gainB = 1.0 / b;
    float R = (float)(gainR / gainG), G = 1.0f, B = (float)(gainB / gainG);
    return new RggbChannelVector(R, G, G, B);
  }catch(Throwable t){ return new RggbChannelVector(1f,1f,1f,1f); }
}
"""
        s = re.sub(r'(createCaptureRequest\(\s*CameraDevice\.TEMPLATE_RECORD\s*\)\s*;\s*)',
                   r'\1\napplyLogManualIfEnabled(builder);\n', s)
        write(cam, s)

# 4) Preferences & arrays for Pro Video menu (create if missing; main prefs include)
addon_prefs = """<?xml version="1.0" encoding="utf-8"?>
<PreferenceScreen xmlns:android="http://schemas.android.com/apk/res/android">
    <SwitchPreference android:key="pref_pro_video_mode"
        android:title="Enable Pro Video (10-bit LOG HEVC)"
        android:defaultValue="false"/>
    <ListPreference android:key="pref_color_profile" android:title="Color Profile"
        android:entries="@array/pref_color_profile_entries"
        android:entryValues="@array/pref_color_profile_values"
        android:defaultValue="canon_log3_cinema"/>
    <ListPreference android:key="pref_hdr_delivery" android:title="HDR Delivery"
        android:entries="@array/pref_hdr_delivery_entries"
        android:entryValues="@array/pref_hdr_delivery_values"
        android:defaultValue="none"/>
    <EditTextPreference android:key="pref_bitrate_mbps" android:title="Bitrate (Mbps)" android:defaultValue="120"/>
    <EditTextPreference android:key="pref_gop_seconds" android:title="GOP (I-frame sec)" android:defaultValue="1"/>
    <ListPreference android:key="pref_wb_quick" android:title="WB Quick Preset"
        android:entries="@array/pref_wb_quick_entries"
        android:entryValues="@array/pref_wb_quick_values"
        android:defaultValue="custom"/>
    <EditTextPreference android:key="pref_wb_cct" android:title="White Balance CCT (K)" android:defaultValue="5600"/>
    <EditTextPreference android:key="pref_exposure_us" android:title="Shutter (microseconds)" android:defaultValue="20833"/>
    <EditTextPreference android:key="pref_iso" android:title="ISO" android:defaultValue="200"/>
    <EditTextPreference android:key="pref_focus_m" android:title="Focus Distance (meters)" android:defaultValue="1.5"/>
</PreferenceScreen>
"""
arrays_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string-array name="pref_color_profile_entries">
        <item>Canon Log 3 (Cinema Gamut)</item>
        <item>ARRI LogC3 (AWG)</item>
        <item>ACEScct (ACEScg)</item>
        <item>Flat (BT.709)</item>
    </string-array>
    <string-array name="pref_color_profile_values">
        <item>canon_log3_cinema</item>
        <item>arri_logc3_awg</item>
        <item>acescct_acescg</item>
        <item>flat_bt709</item>
    </string-array>
    <string-array name="pref_hdr_delivery_entries">
        <item>None (LOG master)</item>
        <item>HLG (Rec.2020)</item>
        <item>PQ / HDR10 (Rec.2020)</item>
    </string-array>
    <string-array name="pref_hdr_delivery_values">
        <item>none</item>
        <item>hlg</item>
        <item>pq</item>
    </string-array>
    <string-array name="pref_wb_quick_entries">
        <item>Custom (use Kelvin below)</item>
        <item>2500 K (Tungsten)</item>
        <item>3200 K (Quartz)</item>
        <item>4300 K (Fluoro)</item>
        <item>5600 K (Daylight)</item>
        <item>6500 K (D65)</item>
        <item>7500 K (Shade)</item>
    </string-array>
    <string-array name="pref_wb_quick_values">
        <item>custom</item>
        <item>2500</item>
        <item>3200</item>
        <item>4300</item>
        <item>5600</item>
        <item>6500</item>
        <item>7500</item>
    </string-array>
</resources>
"""

if not pref_addon.exists():
    write(pref_addon, addon_prefs)
if not arrays.exists():
    write(arrays, arrays_xml)
if pref_main.exists():
    pm = read(pref_main)
    if "opencamera_addon_prefs" not in pm:
        pm = pm.replace("</PreferenceScreen>",
            '    <PreferenceCategory android:title="Pro Video (LOG)">\n'
            '        <PreferenceScreen android:title="LOG / 10-bit Settings">\n'
            '            <include layout="@xml/opencamera_addon_prefs"/>\n'
            '        </PreferenceScreen>\n'
            '    </PreferenceCategory>\n'
            '</PreferenceScreen>')
        write(pref_main, pm)
