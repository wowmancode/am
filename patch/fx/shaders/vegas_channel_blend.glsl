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

float diagonal(float value) {
    return max(0.0, 2.0 * exp2(value) - 1.0);
}

vec3 normalizedRow(vec3 row) {
    float total = row.x + row.y + row.z;
    return total > 0.0 ? row / total : vec3(0.0);
}

void main() {
    vec4 source = texture2D(uTexSampler, clamp(vTexSamplingCoord, 0.0, 1.0));
    vec3 redRow = vec3(diagonal(uControl2), uControl3, uControl4);
    vec3 greenRow = vec3(0.0, diagonal(uControl5), 0.0);
    vec3 blueRow = vec3(uControl6, 0.0, diagonal(uControl7));
    if (uControl8 > 0.5) {
        redRow = normalizedRow(redRow);
        greenRow = normalizedRow(greenRow);
        blueRow = normalizedRow(blueRow);
    }
    vec3 outputRgb = vec3(dot(redRow, source.rgb),
                          dot(greenRow, source.rgb),
                          dot(blueRow, source.rgb));
    gl_FragColor = clamp(mix(source, vec4(outputRgb, source.a),
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
