#include "mainwindow.h"

#include "adbmanager.h"

#include <QHeaderView>
#include <QLabel>
#include <QLineEdit>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QTableWidget>
#include <QVBoxLayout>
#include <QWidget>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QFormLayout>

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent), m_adb(new AdbManager(this))
{
    setWindowTitle(QStringLiteral("ScreenMirror"));
    resize(760, 480);

    auto* central = new QWidget(this);
    auto* layout = new QVBoxLayout(central);
    auto* title = new QLabel(QStringLiteral("ScreenMirror"), central);
    title->setStyleSheet(QStringLiteral("font-size: 24px; font-weight: 600;"));
    layout->addWidget(title);

    m_platformLabel = new QLabel(QStringLiteral("Host: %1").arg(m_adb->hostPlatformName()), central);
    m_adbLabel = new QLabel(QStringLiteral("ADB: %1").arg(m_adb->adbPath().isEmpty() ? QStringLiteral("not found") : m_adb->adbPath()), central);
    m_statusLabel = new QLabel(QStringLiteral("Starting..."), central);
    layout->addWidget(m_platformLabel);
    layout->addWidget(m_adbLabel);
    layout->addWidget(m_statusLabel);

    auto* serverControls = new QHBoxLayout;
    m_startServerButton = new QPushButton(QStringLiteral("Start ADB server"), central);
    m_stopServerButton = new QPushButton(QStringLiteral("Stop ADB server"), central);
    m_refreshButton = new QPushButton(QStringLiteral("Refresh devices"), central);
    m_disconnectButton = new QPushButton(QStringLiteral("Disconnect selected"), central);
    serverControls->addWidget(m_startServerButton);
    serverControls->addWidget(m_stopServerButton);
    serverControls->addWidget(m_refreshButton);
    serverControls->addWidget(m_disconnectButton);
    layout->addLayout(serverControls);

    m_deviceTable = new QTableWidget(0, 4, central);
    m_deviceTable->setHorizontalHeaderLabels({QStringLiteral("Serial"), QStringLiteral("State"), QStringLiteral("Model"), QStringLiteral("Transport")});
    m_deviceTable->horizontalHeader()->setStretchLastSection(true);
    m_deviceTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_deviceTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    layout->addWidget(m_deviceTable, 1);

    auto* wirelessBox = new QGroupBox(QStringLiteral("Wireless ADB"), central);
    auto* wirelessForm = new QFormLayout(wirelessBox);
    m_wirelessTargetEdit = new QLineEdit(wirelessBox);
    m_wirelessTargetEdit->setPlaceholderText(QStringLiteral("192.168.1.20:5555 or pairing host:port"));
    m_pairingCodeEdit = new QLineEdit(wirelessBox);
    m_pairingCodeEdit->setPlaceholderText(QStringLiteral("Pairing code (optional for connect)"));
    auto* wirelessButtons = new QHBoxLayout;
    auto* pairButton = new QPushButton(QStringLiteral("Pair"), wirelessBox);
    auto* connectButton = new QPushButton(QStringLiteral("Connect"), wirelessBox);
    wirelessButtons->addWidget(pairButton);
    wirelessButtons->addWidget(connectButton);
    wirelessForm->addRow(QStringLiteral("Host and port:"), m_wirelessTargetEdit);
    wirelessForm->addRow(QStringLiteral("Pairing code:"), m_pairingCodeEdit);
    wirelessForm->addRow(wirelessButtons);
    layout->addWidget(wirelessBox);

    m_diagnostics = new QPlainTextEdit(central);
    m_diagnostics->setReadOnly(true);
    m_diagnostics->setMaximumBlockCount(500);
    m_diagnostics->setPlaceholderText(QStringLiteral("ADB diagnostics will appear here."));
    layout->addWidget(m_diagnostics, 1);
    setCentralWidget(central);

    connect(m_refreshButton, &QPushButton::clicked, m_adb, &AdbManager::refreshDevices);
    connect(m_startServerButton, &QPushButton::clicked, m_adb, &AdbManager::startServer);
    connect(m_stopServerButton, &QPushButton::clicked, m_adb, &AdbManager::stopServer);
    connect(m_disconnectButton, &QPushButton::clicked, this, [this] {
        const int row = m_deviceTable->currentRow();
        if (row >= 0 && m_deviceTable->item(row, 0))
            m_adb->disconnectDevice(m_deviceTable->item(row, 0)->text());
        else
            showError(QStringLiteral("Select a device before disconnecting."));
    });
    connect(pairButton, &QPushButton::clicked, this, [this] {
        m_adb->pairWireless(m_wirelessTargetEdit->text(), m_pairingCodeEdit->text());
    });
    connect(connectButton, &QPushButton::clicked, this, [this] {
        m_adb->connectWireless(m_wirelessTargetEdit->text());
    });
    connect(m_adb, &AdbManager::devicesUpdated, this, &MainWindow::updateDevices);
    connect(m_adb, &AdbManager::statusMessage, this, [this](const QString& message) {
        m_statusLabel->setText(message);
        m_diagnostics->appendPlainText(QStringLiteral("INFO: %1").arg(message));
    });
    connect(m_adb, &AdbManager::errorMessage, this, &MainWindow::showError);
    connect(m_adb, &AdbManager::versionDetected, this, [this](const QString& version) {
        QString normalized = version;
        normalized.replace('\n', QStringLiteral(" | "));
        m_diagnostics->appendPlainText(QStringLiteral("ADB version: %1").arg(normalized));
    });
    connect(m_adb, &AdbManager::versionDetected, m_adb, &AdbManager::startServer);
    connect(m_adb, &AdbManager::operationBusy, this, [this](bool busy) {
        m_refreshButton->setDisabled(busy);
        m_startServerButton->setDisabled(busy);
        m_stopServerButton->setDisabled(busy);
        m_disconnectButton->setDisabled(busy);
    });

    if (m_adb->adbPath().isEmpty()) {
        showError(m_adb->lastError());
    } else {
        m_adb->checkVersion();
    }
}

void MainWindow::updateDevices(const QVector<AdbDevice>& devices)
{
    m_deviceTable->setRowCount(0);
    for (const AdbDevice& device : devices) {
        const int row = m_deviceTable->rowCount();
        m_deviceTable->insertRow(row);
        m_deviceTable->setItem(row, 0, new QTableWidgetItem(device.serial));
        m_deviceTable->setItem(row, 1, new QTableWidgetItem(device.state));
        m_deviceTable->setItem(row, 2, new QTableWidgetItem(device.model));
        m_deviceTable->setItem(row, 3, new QTableWidgetItem(device.transport));
    }
}

void MainWindow::showError(const QString& message)
{
    if (m_statusLabel)
        m_statusLabel->setText(QStringLiteral("Error: %1").arg(message));
    if (m_diagnostics)
        m_diagnostics->appendPlainText(QStringLiteral("ERROR: %1").arg(message));
}
