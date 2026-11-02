precision highp float;

uniform sampler2D uTexSampler;
uniform float uTime;
uniform float uWidth;
uniform float uHeight;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
varying vec2 vTexSamplingCoord;

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 source = texture2D(uTexSampler, uv);
    float widthPx = max(uWidth, 1.0);
    float heightPx = max(uHeight, 1.0);
    vec2 pixel = vec2(uv.x * widthPx - 0.5,
                      (1.0 - uv.y) * heightPx - 0.5);

    float rate = clamp(0.09 * exp2(uControl2), 0.0, 1.0);
    float strength = clamp(exp2(uControl3), 0.0, 1.0);
    float drift = clamp(0.07 * exp2(uControl4), 0.0, 1.0);
    float edgeSize = clamp(max(uControl5, 0.0) * 0.25, 0.0, 1.0);
    float edgeMode = 1.0;
    if (uControl6 < -0.5) edgeMode = 0.0;
    if (uControl6 > 0.5) edgeMode = 2.0;
    bool horizontal = uControl7 <= 0.5;

    float axisLength = horizontal ? widthPx : heightPx;
    float lineLength = horizontal ? heightPx : widthPx;
    float axisPixel = horizontal ? pixel.x : pixel.y;
    float linePixel = horizontal ? pixel.y : pixel.x;
    float phase = (linePixel / lineLength) *
                  (rate * rate * 20.0 * 6.283) + drift * 30.0 * uTime;
    float wave = sin(phase);
    float amplitude = strength * strength * 0.3;
    float targetPixel = axisPixel + wave * axisLength * amplitude;

    if (edgeMode > 0.5 && edgeMode < 1.5) {
        float pivot = 0.5 - wave * amplitude;
        float position = axisPixel / axisLength;
        float mapped = position < pivot
            ? 0.5 * position / max(pivot, 0.00001)
            : 0.5 + 0.5 * (position - pivot) / max(1.0 - pivot, 0.00001);
        targetPixel = mapped * axisLength;
    }

    float guardPx = floor(axisLength * edgeSize * 0.499);
    float lowPixel = guardPx;
    float highPixel = max(axisLength - guardPx - 1.0, lowPixel);
    bool outside = targetPixel < lowPixel || targetPixel >= highPixel;
    targetPixel = clamp(targetPixel, lowPixel, highPixel);
    float firstPixel = floor(targetPixel);
    float secondPixel = min(firstPixel + 1.0, highPixel);
    float secondWeight = floor((targetPixel - firstPixel) * 255.0);
    float firstWeight = 255.0 - secondWeight;
    vec2 firstUv = uv;
    vec2 secondUv = uv;
    if (horizontal) {
        firstUv.x = (firstPixel + 0.5) / widthPx;
        secondUv.x = (secondPixel + 0.5) / widthPx;
    } else {
        firstUv.y = 1.0 - (firstPixel + 0.5) / heightPx;
        secondUv.y = 1.0 - (secondPixel + 0.5) / heightPx;
    }
    vec4 firstColor = floor(texture2D(uTexSampler,
                                      clamp(firstUv, 0.0, 1.0)) * 255.0 + 0.5);
    vec4 secondColor = floor(texture2D(uTexSampler,
                                       clamp(secondUv, 0.0, 1.0)) * 255.0 + 0.5);
    vec4 warped = floor((firstColor * firstWeight +
                         secondColor * secondWeight) / 255.0 + 0.0001) / 255.0;
    if (edgeMode > 1.5 && outside) warped = vec4(0.0);
    gl_FragColor = clamp(mix(source, warped,
                             clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
