// lib/faz_input_page.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:typed_data'; // Uint8List için
import 'faz_grafik_ekrani.dart'; // FazGrafikEkrani dosyasını import et

class FazInputPage extends StatefulWidget {
  final String selectedElement;
  final Function(Map<String, dynamic>) onCalculationComplete;

  const FazInputPage({
    super.key,
    required this.selectedElement,
    required this.onCalculationComplete,
  });

  @override
  State<FazInputPage> createState() => _FazInputPageState();
}

class _FazInputPageState extends State<FazInputPage> {
  late TextEditingController _soluteController;

  @override
  void initState() {
    super.initState();
    _soluteController = TextEditingController(text: widget.selectedElement);
  }

  final TextEditingController _tempController =
      TextEditingController(text: '700'); // Varsayılan değer
  final TextEditingController _wtXController =
      TextEditingController(text: '5'); // Varsayılan değer (%5)

  bool _isLoading = false;
  String? _errorMessage;

  // Arka uç sunucusunun adresi
  // Eğer emulator kullanıyorsanız 'http://10.0.2.2:8000/calculate_equilibrium'
  // Kendi cihazınızda veya ağda çalışıyorsanız 'http://<bilgisayar_ip_adresin>:8000/calculate_equilibrium'
  final String _backendUrl = 'http://127.0.0.1:8000/phase-diagram';

  @override
  void dispose() {
    _soluteController.dispose();
    _tempController.dispose();
    _wtXController.dispose();
    super.dispose();
  }

  // Hesaplama işlemini başlatan asenkron fonksiyon
  Future<void> _performCalculation() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null; // Önceki hataları temizle
    });

    final String solute = _soluteController.text.trim().toUpperCase();
    final double? tempC = double.tryParse(_tempController.text);
    final double? wtX = double.tryParse(_wtXController.text);

    // Giriş doğrulaması
    if (solute.isEmpty ||
        tempC == null ||
        wtX == null ||
        wtX < 0 ||
        wtX > 100) {
      setState(() {
        _errorMessage =
            'Lütfen geçerli girişler yapın. Sıcaklık ve % Ağırlıkça miktar sayı olmalı ve % miktarı 0-100 arasında olmalı.';
        _isLoading = false;
      });
      return;
    }

    try {
      final response = await http.post(
        Uri.parse(_backendUrl),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'solute': solute,
          'T_C': tempC,
          'wt_x': wtX,
        }),
      );

      setState(() => _isLoading = false); // Yükleme durumunu kapat

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);

        // FazGrafikEkrani'na tüm sonuçları içeren map'i gönder
        widget.onCalculationComplete(data);
      } else {
        final Map<String, dynamic> errorData = json.decode(response.body);
        setState(() {
          _errorMessage = errorData['detail'] ??
              'Hesaplama hatası. Lütfen girişleri kontrol edin.';
        });
      }

      print('Gelen veri: ${response.body}');
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage =
            'Sunucuya bağlanılamadı veya bir hata oluştu: ${e.toString()}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fe-X Termodinamik Uygulaması'),
        centerTitle: true,
        elevation: 4,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(
            bottom: Radius.circular(16),
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Giriş Alanları
            Card(
              elevation: 3,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              margin: const EdgeInsets.only(bottom: 16),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    TextFormField(
                      controller: _soluteController,
                      decoration: InputDecoration(
                        labelText: 'Element Sembolü (Ör: CR, NI)',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8)),
                        prefixIcon: const Icon(Icons.science),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _tempController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: 'Sıcaklık (°C)',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8)),
                        prefixIcon: const Icon(Icons.thermostat),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _wtXController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: '% Ağırlıkça Element Miktarı',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8)),
                        prefixIcon: const Icon(Icons.scale),
                      ),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton.icon(
                      onPressed: _isLoading ? null : _performCalculation,
                      icon: _isLoading
                          ? const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.calculate),
                      label: Text(_isLoading ? 'Hesaplanıyor...' : 'Hesapla'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 30, vertical: 15),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10)),
                        elevation: 5,
                        backgroundColor: Colors.blueAccent,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Hata Mesajı
            if (_errorMessage != null)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade300),
                ),
                child: Text(
                  _errorMessage!,
                  style: TextStyle(
                      color: Colors.red.shade700, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
