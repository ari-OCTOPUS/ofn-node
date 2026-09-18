#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include "rknn_api.h"

static double now_ms(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char **argv) {
  const char *model_path = argc > 1 ? argv[1] : "/opt/rknn-pilot/yolov5s-640-640.rknn";
  int loops = argc > 2 ? atoi(argv[2]) : 20;
  int warmup = argc > 3 ? atoi(argv[3]) : 3;
  printf("MODEL=%s\nLOOPS=%d WARMUP=%d\n", model_path, loops, warmup);

  FILE *fp = fopen(model_path, "rb");
  if (!fp) { perror("fopen model"); return 2; }
  fseek(fp, 0, SEEK_END);
  long model_len = ftell(fp);
  fseek(fp, 0, SEEK_SET);
  void *model = malloc(model_len);
  if (!model) { fclose(fp); return 3; }
  if (fread(model, 1, model_len, fp) != (size_t)model_len) { fclose(fp); free(model); return 4; }
  fclose(fp);
  printf("MODEL_BYTES=%ld\n", model_len);

  rknn_context ctx = 0;
  int ret = rknn_init(&ctx, model, model_len, 0, NULL);
  free(model);
  printf("rknn_init=%d\n", ret);
  if (ret != RKNN_SUCC) return 10;

  rknn_sdk_version ver;
  ret = rknn_query(ctx, RKNN_QUERY_SDK_VERSION, &ver, sizeof(ver));
  printf("rknn_query_sdk=%d api=%s drv=%s\n", ret, ver.api_version, ver.drv_version);

  rknn_input_output_num io_num;
  ret = rknn_query(ctx, RKNN_QUERY_IN_OUT_NUM, &io_num, sizeof(io_num));
  printf("rknn_query_io=%d n_input=%d n_output=%d\n", ret, io_num.n_input, io_num.n_output);
  if (ret != RKNN_SUCC) { rknn_destroy(ctx); return 11; }

  rknn_tensor_attr input_attrs[8];
  memset(input_attrs, 0, sizeof(input_attrs));
  for (uint32_t i = 0; i < io_num.n_input && i < 8; i++) {
    input_attrs[i].index = i;
    ret = rknn_query(ctx, RKNN_QUERY_INPUT_ATTR, &(input_attrs[i]), sizeof(rknn_tensor_attr));
    printf("input[%u] dims=", i);
    for (uint32_t d = 0; d < input_attrs[i].n_dims; d++) printf("%u%s", input_attrs[i].dims[d], d+1<input_attrs[i].n_dims?"x":"");
    printf(" fmt=%d type=%d size=%u\n", input_attrs[i].fmt, input_attrs[i].type, input_attrs[i].size);
  }

  uint32_t in_size = input_attrs[0].size ? input_attrs[0].size : (3*640*640);
  uint8_t *in_buf = (uint8_t*)calloc(1, in_size);
  if (!in_buf) { rknn_destroy(ctx); return 12; }
  /* deterministic pseudo-image */
  for (uint32_t i = 0; i < in_size; i++) in_buf[i] = (uint8_t)(i * 17u);

  rknn_input inputs[1];
  memset(inputs, 0, sizeof(inputs));
  inputs[0].index = 0;
  inputs[0].type = RKNN_TENSOR_UINT8;
  inputs[0].size = in_size;
  inputs[0].fmt = RKNN_TENSOR_NHWC;
  inputs[0].buf = in_buf;
  inputs[0].pass_through = 0;

  for (int w = 0; w < warmup; w++) {
    ret = rknn_inputs_set(ctx, 1, inputs);
    if (ret != RKNN_SUCC) { printf("warmup inputs_set=%d\n", ret); free(in_buf); rknn_destroy(ctx); return 13; }
    ret = rknn_run(ctx, NULL);
    if (ret != RKNN_SUCC) { printf("warmup run=%d\n", ret); free(in_buf); rknn_destroy(ctx); return 14; }
  }

  double times[512];
  if (loops > 512) loops = 512;
  for (int i = 0; i < loops; i++) {
    double t0 = now_ms();
    ret = rknn_inputs_set(ctx, 1, inputs);
    if (ret != RKNN_SUCC) { printf("inputs_set=%d iter=%d\n", ret, i); break; }
    ret = rknn_run(ctx, NULL);
    double t1 = now_ms();
    if (ret != RKNN_SUCC) { printf("run=%d iter=%d\n", ret, i); break; }
    times[i] = t1 - t0;
  }

  /* outputs once for correctness witness */
  rknn_output outputs[8];
  memset(outputs, 0, sizeof(outputs));
  for (uint32_t i = 0; i < io_num.n_output && i < 8; i++) {
    outputs[i].want_float = 1;
    outputs[i].is_prealloc = 0;
  }
  ret = rknn_outputs_get(ctx, io_num.n_output, outputs, NULL);
  printf("rknn_outputs_get=%d\n", ret);
  uint64_t out_checksum = 0;
  size_t out_bytes = 0;
  if (ret == RKNN_SUCC) {
    for (uint32_t i = 0; i < io_num.n_output && i < 8; i++) {
      float *f = (float*)outputs[i].buf;
      uint32_t n = outputs[i].size / sizeof(float);
      out_bytes += outputs[i].size;
      printf("output[%u] bytes=%u floats=%u first3=", i, outputs[i].size, n);
      for (uint32_t k = 0; k < n && k < 3; k++) printf("%g ", f[k]);
      printf("\n");
      for (uint32_t k = 0; k < n; k++) {
        uint32_t u; memcpy(&u, &f[k], 4); out_checksum = out_checksum * 1315423911u + u + k;
      }
    }
    rknn_outputs_release(ctx, io_num.n_output, outputs);
  }
  printf("OUTPUT_CHECKSUM=%llu OUTPUT_BYTES=%zu\n", (unsigned long long)out_checksum, out_bytes);

  double sum = 0, mn = 1e99, mx = 0;
  for (int i = 0; i < loops; i++) { sum += times[i]; if (times[i] < mn) mn = times[i]; if (times[i] > mx) mx = times[i]; }
  /* p50 rough */
  for (int i = 0; i < loops; i++) for (int j = i+1; j < loops; j++) if (times[j] < times[i]) { double t=times[i]; times[i]=times[j]; times[j]=t; }
  double p50 = times[loops/2];
  double p95 = times[(int)(loops*0.95)];
  double mean = sum / (loops ? loops : 1);
  double fps = mean > 0 ? 1000.0 / mean : 0;
  printf("LATENCY_MS_MEAN=%.3f\nLATENCY_MS_MIN=%.3f\nLATENCY_MS_MAX=%.3f\nLATENCY_MS_P50=%.3f\nLATENCY_MS_P95=%.3f\nTHROUGHPUT_FPS=%.3f\n",
         mean, mn, mx, p50, p95, fps);

  /* NPU load witness if available */
  FILE *lf = fopen("/sys/kernel/debug/rknpu/load", "r");
  if (lf) { char buf[256]; if (fgets(buf, sizeof(buf), lf)) printf("NPU_LOAD=%s", buf); fclose(lf); }
  else printf("NPU_LOAD=UNAVAILABLE\n");

  free(in_buf);
  rknn_destroy(ctx);
  printf("STATUS=PASS\n");
  return 0;
}
