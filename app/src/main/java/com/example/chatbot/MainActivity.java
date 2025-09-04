package com.example.chatbot;

import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.Call;

import org.json.JSONObject;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private static final String PATH_ASK = "/ask";
    private static final String PATH_TRANSLATE = "/translate";
    private static final String PATH_SUMMARY = "/summary";

    TextView tvChat;
    Button btnTranslate, btnSummary;
    EditText edtInput, edtServerIp;
    ImageButton btnSend, btnCancel;
    OkHttpClient client;
    Call currentCall;
    String lastAnswer = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvChat = findViewById(R.id.tvChat);
        btnTranslate = findViewById(R.id.btnTranslate);
        btnSummary = findViewById(R.id.btnSummary);
        edtInput = findViewById(R.id.edtInput);
        edtServerIp = findViewById(R.id.edtServerIp);
        btnSend = findViewById(R.id.btnSend);
        btnCancel = findViewById(R.id.btnCancel);

        tvChat.setMovementMethod(new ScrollingMovementMethod());
        tvChat.setText("Xin chào! Hãy đặt câu hỏi về sức khỏe...");
        edtServerIp.setText("http://192.168.1.10:5050");

        client = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .build();

        btnSend.setOnClickListener(v -> sendHealthQuestion());
        btnCancel.setOnClickListener(v -> {
            if (currentCall != null && !currentCall.isCanceled()) {
                currentCall.cancel();
                tvChat.setText("Đã hủy thao tác!");
                enableButtons();
                toggleSendCancel(true);
            }
        });

        btnTranslate.setOnClickListener(v -> {
            if (!lastAnswer.isEmpty()) {
                translateText(lastAnswer);
            } else {
                showToast("Chưa có nội dung để dịch.");
            }
        });

        btnSummary.setOnClickListener(v -> {
            if (!lastAnswer.isEmpty()) {
                summarizeText(lastAnswer);
            } else {
                showToast("Chưa có nội dung để tóm tắt.");
            }
        });

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });
    }

    private void sendHealthQuestion() {
        String question = edtInput.getText().toString().trim();
        String baseUrl = edtServerIp.getText().toString().trim();
        if (question.isEmpty()) {
            showToast("Vui lòng nhập câu hỏi.");
            return;
        }
        if (baseUrl.isEmpty()) {
            showToast("Vui lòng nhập địa chỉ server.");
            return;
        }

        edtInput.setText("");
        tvChat.setText("Đang tư vấn sức khỏe...");
        disableButtons();
        toggleSendCancel(false);

        sendRequest(baseUrl + PATH_ASK, "question", question, "health");
    }

    private void translateText(String text) {
        String baseUrl = edtServerIp.getText().toString().trim();
        if (baseUrl.isEmpty()) {
            showToast("Vui lòng nhập địa chỉ server.");
            return;
        }

        tvChat.setText("Đang dịch...");
        disableButtons();
        toggleSendCancel(false);

        sendRequest(baseUrl + PATH_TRANSLATE, "text", text, "translate");
    }

    private void summarizeText(String text) {
        String baseUrl = edtServerIp.getText().toString().trim();
        if (baseUrl.isEmpty()) {
            showToast("Vui lòng nhập địa chỉ server.");
            return;
        }

        tvChat.setText("Đang tóm tắt...");
        disableButtons();
        toggleSendCancel(false);

        sendRequest(baseUrl + PATH_SUMMARY, "text", text, "summary");
    }

    private void sendRequest(String url, String fieldName, String content, String requestType) {
        try {
            JSONObject json = new JSONObject();
            json.put(fieldName, content);
            if ("translate".equals(requestType) || "summary".equals(requestType)) {
                json.put("target_language", "French");
            }

            RequestBody body = RequestBody.create(
                    json.toString(),
                    MediaType.parse("application/json; charset=utf-8")
            );

            Request request = new Request.Builder()
                    .url(url)
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .addHeader("Accept", "application/json")
                    .build();

            currentCall = client.newCall(request);

            new Thread(() -> {
                try {
                    Response response = currentCall.execute();
                    if (response.isSuccessful() && response.body() != null) {
                        String responseBody = response.body().string();
                        JSONObject obj = new JSONObject(responseBody);
                        String status = obj.optString("status", "unknown");
                        String answer = obj.optString("answer", "Không có phản hồi");

                        if ("health".equals(requestType)) {
                            lastAnswer = answer;
                        }

                        String formattedAnswer = formatAnswer(requestType, answer, status);

                        runOnUiThread(() -> {
                            tvChat.setText(formattedAnswer);
                            enableButtons();
                            toggleSendCancel(true);
                        });
                    } else {
                        String errorMsg = "Lỗi server: " + response.code();
                        runOnUiThread(() -> {
                            tvChat.setText(errorMsg);
                            enableButtons();
                            toggleSendCancel(true);
                        });
                    }
                } catch (IOException e) {
                    runOnUiThread(() -> {
                        tvChat.setText(currentCall.isCanceled() ? "Đã hủy thao tác!" : "Lỗi kết nối: " + e.getMessage());
                        enableButtons();
                        toggleSendCancel(true);
                    });
                } catch (Exception e) {
                    runOnUiThread(() -> {
                        tvChat.setText("Lỗi không xác định: " + e.getMessage());
                        enableButtons();
                        toggleSendCancel(true);
                    });
                }
            }).start();
        } catch (Exception e) {
            tvChat.setText("Lỗi tạo request: " + e.getMessage());
            enableButtons();
            toggleSendCancel(true);
        }
    }

    private String formatAnswer(String type, String answer, String status) {
        String prefix = "";
        if ("partial_success".equals(status)) {
            prefix = "[Cảnh báo] ";
        } else if ("success".equals(status)) {
            prefix = "[Thành công] ";
        }

        switch (type) {
            case "health":
                return prefix + "Tư vấn:\n\n" + answer + "\n\nBạn có thể dịch hoặc tóm tắt nội dung.";
            case "translate":
                return prefix + "Bản dịch:\n\n" + answer;
            case "summary":
                return prefix + "Tóm tắt:\n\n" + answer;
            default:
                return prefix + answer;
        }
    }

    private void toggleSendCancel(boolean showSend) {
        runOnUiThread(() -> {
            btnSend.setVisibility(showSend ? ImageButton.VISIBLE : ImageButton.GONE);
            btnCancel.setVisibility(showSend ? Button.GONE : Button.VISIBLE);
        });
    }

    private void disableButtons() {
        runOnUiThread(() -> {
            btnSend.setEnabled(false);
            btnTranslate.setEnabled(false);
            btnSummary.setEnabled(false);
        });
    }

    private void enableButtons() {
        runOnUiThread(() -> {
            btnSend.setEnabled(true);
            btnTranslate.setEnabled(true);
            btnSummary.setEnabled(true);
        });
    }

    private void showToast(String message) {
        runOnUiThread(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show());
    }
}
