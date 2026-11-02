precision highp float;

uniform sampler2D uTexSampler;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
uniform float uControl8;
varying vec2 vTexSamplingCoord;

vec2 wheel(float angleControl, float radiusControl, float weight) {
    float angle = 3.14159265359 * angleControl;
    float radius = clamp(0.5 * radiusControl, 0.0, 1.0);
    float amount = 0.5 * weight * radius * radius;
    return amount * vec2(cos(angle), sin(angle));
}

void main() {
    vec4 source = texture2D(uTexSampler, clamp(vTexSamplingCoord, 0.0, 1.0));
    float neutral = abs(uControl2) + abs(uControl3) + abs(uControl4) +
                    abs(uControl5) + abs(uControl6) + abs(uControl7) +
                    abs(uControl8);
    if (neutral < 0.000001) {
        gl_FragColor = clamp(source, 0.0, 1.0);
        return;
    }
    float y = dot(source.rgb, vec3(0.299, 0.587, 0.114));
    float u = 0.492 * (source.b - y);
    float v = 0.877 * (source.r - y);
    vec2 shift = wheel(uControl2, uControl3, exp(-6.2383246251 * y * y));
    float middle = y - 0.5;
    shift += wheel(uControl4, uControl5, exp(-17.3010380623 * middle * middle));
    float high = y - 1.0;
    shift += wheel(uControl6, uControl7, exp(-6.2383246251 * high * high));
    u = (u + shift.x) * exp2(uControl8);
    v = (v + shift.y) * exp2(uControl8);
    vec3 effect = vec3(y + 1.1402509212 * v,
                       y - 0.3947313428 * u - 0.5808091760 * v,
                       y + 2.0325202942 * u);
    gl_FragColor = clamp(mix(source, vec4(effect, source.a),
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
