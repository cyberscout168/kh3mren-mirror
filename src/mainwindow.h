#pragma once

#include <QMainWindow>

#include "adbmanager.h"

class QLabel;
class QTableWidget;
class QPushButton;
class QLineEdit;
class QPlainTextEdit;

class MainWindow final : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget* parent = nullptr);

private:
    void updateDevices(const QVector<AdbDevice>& devices);
    void showError(const QString& message);

    AdbManager* m_adb = nullptr;
    QLabel* m_platformLabel = nullptr;
    QLabel* m_adbLabel = nullptr;
    QLabel* m_statusLabel = nullptr;
    QTableWidget* m_deviceTable = nullptr;
    QPushButton* m_refreshButton = nullptr;
    QPushButton* m_startServerButton = nullptr;
    QPushButton* m_stopServerButton = nullptr;
    QPushButton* m_disconnectButton = nullptr;
    QLineEdit* m_wirelessTargetEdit = nullptr;
    QLineEdit* m_pairingCodeEdit = nullptr;
    QPlainTextEdit* m_diagnostics = nullptr;
};

