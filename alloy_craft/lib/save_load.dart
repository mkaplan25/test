import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:file_picker/file_picker.dart';

Map<String, dynamic> currentProjectData = {
  "proje_adi": "Yeni Proje",
  "mod": "Single Point",
  "base_element": "FE",
  "elements": [],
  "temperature": null,
  "pressure": null,
  "akis": [],
  "sonuclar": {},
};

/// 📌 Dosya konumunu kullanıcı seçerek kaydet (.alloy)
Future<void> saveAlloyWithPicker() async {
  try {
    String? outputPath = await FilePicker.platform.saveFile(
      dialogTitle: 'Kaydetmek için dosya ismi seçin',
      fileName: "${currentProjectData['proje_adi'] ?? 'alloy_project'}.alloy",
      type: FileType.custom,
      allowedExtensions: ['alloy'],
    );

    if (outputPath == null) return; // Kullanıcı iptal etti

    final file = File(outputPath);
    final jsonContent = jsonEncode(currentProjectData);
    await file.writeAsString(jsonContent);

    print("✅ Kaydedildi: $outputPath");
  } catch (e) {
    print("❌ Kaydetme hatası: $e");
  }
}

/// 📥 Kullanıcının seçtiği .alloy dosyasını yükle
Future<Map<String, dynamic>?> loadAlloyWithPicker() async {
  try {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      dialogTitle: 'Bir .alloy dosyası seçin',
      type: FileType.custom,
      allowedExtensions: ['alloy'],
    );

    if (result == null) return null; // Kullanıcı iptal etti

    final file = File(result.files.single.path!);
    final jsonContent = await file.readAsString();
    final data = jsonDecode(jsonContent);

    currentProjectData = Map<String, dynamic>.from(data);
    print("📥 Yüklendi: ${result.files.single.name}");
    return currentProjectData;
  } catch (e) {
    print("❌ Yükleme hatası: $e");
    return null;
  }
}
