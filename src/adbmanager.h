#pragma once

#include <QObject>
#include <QProcess>
#include <QString>
#include <QVector>

#include <functional>

struct AdbDevice {
    QString serial;
    QString state;
    QString transport;
    QString model;
    QString product;
};

class AdbManager final : public QObject {
    Q_OBJECT

public:
    explicit AdbManager(QObject* parent = nullptr);

    QString adbPath() const;
    QString hostPlatformName() const;
    QString lastError() const;
    QVector<AdbDevice> devices() const;

public slots:
    void checkVersion();
    void startServer();
    void stopServer();
    void refreshDevices();
    void connectWireless(const QString& hostPort);
    void pairWireless(const QString& hostPort, const QString& pairingCode);
    void disconnectDevice(const QString& serial);

signals:
    void statusMessage(const QString& message);
    void errorMessage(const QString& message);
    void versionDetected(const QString& version);
    void devicesUpdated(const QVector<AdbDevice>& devices);
    void operationBusy(bool busy);

private:
    void run(const QStringList& arguments, std::function<void(const QByteArray&, const QByteArray&, int)> finished);
    void setError(const QString& message);
    QString m_adbPath;
    QString m_lastError;
    QVector<AdbDevice> m_devices;
    QProcess* m_process = nullptr;
};

